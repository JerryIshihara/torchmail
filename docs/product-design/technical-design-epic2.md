# Technical Design: Epic 2 - Professor & Research Database

## Architecture Overview

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│               Data Collection Pipeline                        │
│  • Web Scrapers (University directories)                    │
│  • API Integrations (arXiv, Google Scholar)                 │
│  • Manual Entry Interface                                   │
│  • Data Import/Export Tools                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│               Data Processing Engine                          │
│  • Data Cleaning & Normalization                            │
│  • Entity Extraction & Linking                              │
│  • Duplicate Detection & Merging                            │
│  • Quality Validation                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│               Research Intelligence Service                   │
│  • Paper Analysis & Topic Modeling                          │
│  • Research Trend Detection                                 │
│  • Grant/Funding Opportunity Detection                      │
│  • Real-time Updates                                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│               Search & Discovery API                         │
│  • Elasticsearch Integration                                │
│  • Advanced Filtering & Faceting                            │
│  • Semantic Search                                          │
│  • Recommendation Endpoints                                 │
└─────────────────────────────────────────────────────────────┘
```

## Milestone 2.1: Core Database MVP

### Database Schema
```sql
-- Professors
CREATE TABLE professors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255),  -- From source system
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    title VARCHAR(200),
    department_id UUID REFERENCES departments(id),
    university_id UUID REFERENCES universities(id),
    office_location TEXT,
    website_url TEXT,
    research_interests TEXT[],  -- Array of research interests
    biography TEXT,
    photo_url TEXT,
    data_source VARCHAR(100),  -- 'manual', 'scraper', 'api'
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for search
    INDEX idx_professors_name (last_name, first_name),
    INDEX idx_professors_university (university_id),
    INDEX idx_professors_research (research_interests)
);

-- Universities
CREATE TABLE universities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100),
    website_url TEXT,
    ranking_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Departments
CREATE TABLE departments (
    id UUID PRIMARY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES universities(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    website_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_departments_university (university_id)
);

-- Research Papers
CREATE TABLE research_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE,  -- arXiv ID, DOI, etc.
    title TEXT NOT NULL,
    abstract TEXT,
    authors JSONB,  -- Array of author objects
    publication_date DATE,
    venue VARCHAR(255),
    citation_count INTEGER DEFAULT 0,
    pdf_url TEXT,
    source VARCHAR(50),  -- 'arxiv', 'google_scholar', 'manual'
    embedding VECTOR(384),  -- For semantic search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Full-text search index
    INDEX idx_papers_title_gin (to_tsvector('english', title)),
    INDEX idx_papers_abstract_gin (to_tsvector('english', abstract))
);

-- Professor-Paper Relationships
CREATE TABLE professor_papers (
    professor_id UUID REFERENCES professors(id),
    paper_id UUID REFERENCES research_papers(id),
    author_position INTEGER,  -- Position in author list
    is_corresponding BOOLEAN DEFAULT false,
    PRIMARY KEY (professor_id, paper_id)
);
```

### API Endpoints
```typescript
// Professor Management
GET    /api/v1/professors
POST   /api/v1/professors
GET    /api/v1/professors/:id
PUT    /api/v1/professors/:id
DELETE /api/v1/professors/:id

// Search Endpoints
GET /api/v1/search/professors
Query Parameters:
- q: search query
- university_id: filter by university
- department_id: filter by department
- research_interests: array of interests
- page: page number
- limit: results per page

// Research Papers
GET    /api/v1/papers
POST   /api/v1/papers/import  // Bulk import
GET    /api/v1/papers/:id
GET    /api/v1/professors/:id/papers

// University/Department Management
GET    /api/v1/universities
GET    /api/v1/universities/:id/departments
```

### Data Import Service
```python
# data_importer.py
class DataImporter:
    def __init__(self, db_session):
        self.db = db_session
        self.scrapers = {
            'university': UniversityDirectoryScraper(),
            'arxiv': ArxivAPIClient(),
            'google_scholar': GoogleScholarScraper()
        }
    
    async def import_from_source(self, source_type: str, source_config: Dict) -> ImportResult:
        scraper = self.scrapers.get(source_type)
        if not scraper:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # Fetch data from source
        raw_data = await scraper.fetch_data(source_config)
        
        # Process and normalize
        processed_data = await self._process_raw_data(raw_data, source_type)
        
        # Import to database
        import_stats = await self._import_to_database(processed_data)
        
        return ImportResult(
            source=source_type,
            records_processed=len(processed_data),
            records_imported=import_stats['imported'],
            errors=import_stats['errors']
        )
    
    async def _process_raw_data(self, raw_data: List[Dict], source_type: str) -> List[Dict]:
        processed = []
        for item in raw_data:
            try:
                # Normalize based on source type
                normalized = self._normalize_item(item, source_type)
                
                # Validate required fields
                if self._validate_item(normalized):
                    processed.append(normalized)
            except Exception as e:
                logger.error(f"Error processing item: {e}")
        
        return processed
```

## Milestone 2.2: Automated Data Collection

### Distributed Web Scraping System
```python
# scraper_orchestrator.py
class ScraperOrchestrator:
    def __init__(self, redis_client, celery_app):
        self.redis = redis_client
        self.celery = celery_app
        self.scraping_queue = "scraping_tasks"
        
    async def schedule_university_scraping(self, university_ids: List[str]):
        """Schedule scraping tasks for multiple universities"""
        tasks = []
        
        for university_id in university_ids:
            # Check rate limits
            if not await self._check_rate_limit(university_id):
                continue
            
            # Create scraping task
            task = {
                'task_id': str(uuid.uuid4()),
                'university_id': university_id,
                'type': 'faculty_directory',
                'priority': 'high',
                'scheduled_at': datetime.utcnow()
            }
            
            # Queue task
            await self.redis.rpush(self.scraping_queue, json.dumps(task))
            tasks.append(task['task_id'])
        
        return tasks
    
    @celery.task(bind=True, max_retries=3)
    def scrape_university_directory(self, university_id: str):
        """Celery task for scraping university directory"""
        try:
            scraper = UniversityDirectoryScraper()
            
            # Get university configuration
            university = University.objects.get(id=university_id)
            config = university.scraping_config
            
            # Execute scraping
            faculty_data = scraper.scrape(config.url, config.selectors)
            
            # Process and store results
            processor = FacultyDataProcessor()
            processed_data = processor.process(faculty_data)
            
            # Update database
            self._update_professor_database(processed_data, university_id)
            
            # Update scraping statistics
            self._update_scraping_stats(university_id, len(processed_data))
            
        except Exception as e:
            logger.error(f"Scraping failed for {university_id}: {e}")
            raise self.retry(exc=e, countdown=60)
```

### Research Paper Aggregation Service
```python
# paper_aggregator.py
class PaperAggregator:
    def __init__(self):
        self.clients = {
            'arxiv': ArxivClient(),
            'semantic_scholar': SemanticScholarClient(),
            'crossref': CrossrefClient()
        }
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
    
    async def aggregate_professor_papers(self, professor: Professor) -> List[ResearchPaper]:
        papers = []
        
        # Search by author name
        for source_name, client in self.clients.items():
            try:
                source_papers = await client.search_author(
                    name=f"{professor.first_name} {professor.last_name}",
                    affiliation=professor.university.name
                )
                
                # Filter and deduplicate
                filtered_papers = await self._filter_existing_papers(source_papers)
                papers.extend(filtered_papers)
                
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
        
        # Generate embeddings for semantic search
        for paper in papers:
            paper.embedding = self.embedding_model.encode(
                f"{paper.title} {paper.abstract}"
            )
        
        return papers
    
    async def _filter_existing_papers(self, papers: List[Dict]) -> List[Dict]:
        """Filter out papers already in database"""
        existing_ids = await self._get_existing_paper_ids(papers)
        return [p for p in papers if p['external_id'] not in existing_ids]
```

### Data Quality Pipeline
```python
# data_quality_pipeline.py
class DataQualityPipeline:
    def __init__(self):
        self.validators = [
            RequiredFieldValidator(),
            EmailFormatValidator(),
            PhoneFormatValidator(),
            DuplicateDetector(),
            ConsistencyValidator()
        ]
        self.fixers = {
            'email': EmailFixer(),
            'phone': PhoneFixer(),
            'name': NameNormalizer()
        }
    
    async def validate_and_fix(self, data_batch: List[Dict]) -> QualityReport:
        report = QualityReport()
        
        for item in data_batch:
            item_report = ItemQualityReport(item_id=item.get('id'))
            
            # Run validators
            for validator in self.validators:
                violations = validator.validate(item)
                if violations:
                    item_report.add_violations(violations)
            
            # Attempt automatic fixes
            if item_report.has_violations():
                fixed_item = await self._attempt_fixes(item, item_report.violations)
                if fixed_item:
                    item_report.fixed_item = fixed_item
                    item_report.fix_applied = True
            
            report.add_item_report(item_report)
        
        return report
    
    async def _attempt_fixes(self, item: Dict, violations: List[Violation]) -> Optional[Dict]:
        fixed_item = item.copy()
        
        for violation in violations:
            fixer = self.fixers.get(violation.field_type)
            if fixer:
                try:
                    fixed_value = fixer.fix(violation.field_value, violation.rule)
                    fixed_item[violation.field_name] = fixed_value
                except FixError:
                    # Cannot fix automatically
                    return None
        
        return fixed_item
```

## Milestone 2.3: Real-time Research Intelligence

### Real-time Update Service
```python
# realtime_update_service.py
class RealtimeUpdateService:
    def __init__(self, kafka_producer, redis_client):
        self.producer = kafka_producer
        self.redis = redis_client
        self.update_topics = {
            'new_papers': 'research.papers.new',
            'updated_profiles': 'research.profiles.updated',
            'trend_alerts': 'research.trends.alerts'
        }
    
    async def monitor_updates(self):
        """Monitor various sources for updates"""
        while True:
            try:
                # Check arXiv for new papers
                new_papers = await self._check_arxiv_updates()
                if new_papers:
                    await self._publish_updates('new_papers', new_papers)
                
                # Check university directory changes
                profile_updates = await self._check_profile_updates()
                if profile_updates:
                    await self._publish_updates('updated_profiles', profile_updates)
                
                # Analyze for trends
                trends = await self._analyze_trends()
                if trends:
                    await self._publish_updates('trend_alerts', trends)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in update monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_arxiv_updates(self) -> List[Dict]:
        """Check arXiv for new papers in tracked categories"""
        categories = await self._get_tracked_categories()
        new_papers = []
        
        for category in categories:
            papers = await self.arxiv_client.get_recent_papers(
                category=category,
                hours=24  # Last 24 hours
            )
            
            # Filter for relevant professors
            relevant_papers = await self._filter_relevant_papers(papers)
            new_papers.extend(relevant_papers)
        
        return new_papers
```

### Research Trend Detection
```python
# trend_detector.py
class TrendDetector:
    def __init__(self):
        self.topic_model = BERTopic()
        self.change_point_detector = ChangePointDetector()
        
    async def detect_trends(self, time_window_days: int = 30) -> List[ResearchTrend]:
        # Get papers from time window
        papers = await self._get_papers_by_time_window(time_window_days)
        
        if not papers:
            return []
        
        # Extract topics
        documents = [f"{p.title} {p.abstract}" for p in papers]
        topics, probabilities = self.topic_model.fit_transform(documents)
        
        # Analyze topic trends over time
        trends = []
        for topic_id in set(topics):
            topic_papers = [p for p, t in zip(papers, topics) if t == topic_id]
            
            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(topic_papers)
            
            # Detect change points
            change_points = self.change_point_detector.detect(
                [p.publication_date for p in topic_papers]
            )
            
            if growth_rate > 0.5 or change_points:  # Significant growth
                trend = ResearchTrend(
                    topic_id=topic_id,
                    topic_name=self.topic_model.get_topic(topic_id),
                    growth_rate=growth_rate,
                    paper_count=len(topic_papers),
                    change_points=change_points,
                    key_papers=topic_papers[:5]  # Top 5 papers
                )
                trends.append(trend)
        
        return trends
    
    def _calculate_growth_rate(self, papers: List[ResearchPaper]) -> float:
        """Calculate monthly growth rate of papers in topic"""
        if len(papers) < 2:
            return 0.0
        
        # Group by month
        monthly_counts = defaultdict(int)
        for paper in papers:
            month_key = paper.publication_date.strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        # Calculate growth rate
        months = sorted(monthly_counts.keys())
        if len(months) < 2:
            return 0.0
        
        counts = [monthly_counts[m] for m in months]
        growth_rates = [
            (counts[i] - counts[i-1]) / counts[i-1] 
            for i in range(1, len(counts))
        ]
        
        return sum(growth_rates) / len(growth_rates)
```

### Grant/Funding Detection Service
```python
# funding_detector.py
class FundingDetector:
    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.funding_agencies = self._load_funding_agencies()
        
    async def detect_funding_opportunities(
        self, 
        research_area: str
    ) -> List[FundingOpportunity]:
        opportunities = []
        
        # Check various sources
        sources = [
            self._check_grants_gov,
            self._check_nsf_grants,
            self._check_private_foundations
        ]
        
        for source_check in sources:
            try:
                source_opportunities = await source_check(research_area)
                opportunities.extend(source_opportunities)
            except Exception as e:
                logger.error(f"Error checking funding source: {e}")
        
        # Rank opportunities by relevance
        ranked_opportunities = self._rank_by_relevance(opportunities, research_area)
        
        return ranked_opportunities[:10]  # Return top 10
    
    async def _check_grants_gov(self, research_area: str) -> List[FundingOpportunity]:
        """Check grants.gov for opportunities"""
        params = {
            'keyword': research_area,
            'postedFrom': (datetime.now() - timedelta(days=30)).isoformat(),
            'postedTo': datetime.now().isoformat()
        }
