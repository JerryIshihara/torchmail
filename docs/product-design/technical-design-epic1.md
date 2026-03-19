# Technical Design: Epic 1 - AI-Powered Email Generation Core

## Architecture Overview

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  • Email Composition Interface                              │
│  • Template Library                                         │
│  • Preview & Editing Tools                                  │
│  • A/B Testing Dashboard                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS/WebSocket
┌─────────────────▼───────────────────────────────────────────┐
│                    API Gateway                               │
│  • Request Routing                                          │
│  • Authentication/Authorization                             │
│  • Rate Limiting                                            │
│  • Request Validation                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ gRPC/HTTP
┌─────────────────▼───────────────────────────────────────────┐
│               Email Generation Service                       │
│  • Template Management                                      │
│  • Personalization Engine                                   │
│  • AI Integration (OpenAI, Anthropic)                       │
│  • Email Validation & Sanitization                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│               Optimization Service                           │
│  • A/B Testing Framework                                    │
│  • Performance Analytics                                    │
│  • ML Model Serving                                         │
│  • Recommendation Engine                                    │
└─────────────────────────────────────────────────────────────┘
```

## Milestone 1.1: Basic Email Generator MVP

### Database Schema
```sql
-- Email Templates
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Generated Emails
CREATE TABLE generated_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    template_id UUID REFERENCES email_templates(id),
    content TEXT NOT NULL,
    variables_used JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Email Variables
CREATE TABLE email_variables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    default_value TEXT,
    validation_regex TEXT,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints
```typescript
// Email Generation API
POST /api/v1/emails/generate
Request:
{
  "template_id": "uuid",
  "variables": {
    "professor_name": "Dr. Jane Smith",
    "research_area": "Machine Learning",
    "student_background": "CS undergraduate with ML experience"
  },
  "tone": "formal" | "enthusiastic" | "concise"
}

Response:
{
  "email_id": "uuid",
  "content": "Generated email content...",
  "variables_used": {...},
  "generated_at": "timestamp"
}

// Template Management
GET    /api/v1/templates
POST   /api/v1/templates
GET    /api/v1/templates/:id
PUT    /api/v1/templates/:id
DELETE /api/v1/templates/:id

// Email History
GET /api/v1/emails/history
GET /api/v1/emails/:id
```

### AI Integration Service
```python
# email_generation_service.py
class EmailGenerationService:
    def __init__(self, openai_api_key: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
        
    async def generate_email(
        self,
        template: EmailTemplate,
        variables: Dict[str, str],
        tone: str = "formal"
    ) -> GeneratedEmail:
        # Construct prompt
        prompt = self._construct_prompt(template, variables, tone)
        
        # Call OpenAI API
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes professional academic emails."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse and validate response
        email_content = response.choices[0].message.content
        return self._validate_and_format_email(email_content, template, variables)
    
    def _construct_prompt(self, template, variables, tone):
        return f"""
        Write a {tone} email to a professor about a research assistant position.
        
        Template: {template.content}
        
        Variables:
        {json.dumps(variables, indent=2)}
        
        Requirements:
        1. Personalize using all provided variables
        2. Maintain {tone} tone throughout
        3. Keep length between 150-300 words
        4. Include proper academic salutations
        5. End with professional closing
        """
```

### Frontend Components
```typescript
// EmailComposer.tsx
interface EmailComposerProps {
  template: EmailTemplate;
  onGenerate: (email: GeneratedEmail) => void;
}

const EmailComposer: React.FC<EmailComposerProps> = ({ template, onGenerate }) => {
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [tone, setTone] = useState<'formal' | 'enthusiastic' | 'concise'>('formal');
  const [loading, setLoading] = useState(false);
  
  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/emails/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_id: template.id, variables, tone })
      });
      const email = await response.json();
      onGenerate(email);
    } catch (error) {
      console.error('Failed to generate email:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="email-composer">
      <TemplatePreview template={template} />
      <VariableInputs 
        variables={template.variables}
        values={variables}
        onChange={setVariables}
      />
      <ToneSelector value={tone} onChange={setTone} />
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Email'}
      </button>
    </div>
  );
};
```

## Milestone 1.2: Advanced Personalization Engine

### Research Paper Analysis Service
```python
# research_analyzer.py
class ResearchAnalyzer:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")
        
    async def analyze_research_papers(self, professor_id: str) -> ResearchProfile:
        # Fetch papers from arXiv/Google Scholar
        papers = await self._fetch_papers(professor_id)
        
        # Extract key information
        research_profile = ResearchProfile(professor_id=professor_id)
        
        for paper in papers:
            # Extract entities (methods, datasets, concepts)
            entities = self.ner_pipeline(paper.abstract)
            
            # Generate embeddings for semantic search
            embedding = self.embedding_model.encode(paper.abstract)
            
            # Analyze research focus
            topics = self._extract_topics(paper)
            
            research_profile.add_paper(
                paper_id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                year=paper.year,
                entities=entities,
                embedding=embedding,
                topics=topics
            )
        
        return research_profile
    
    def _extract_topics(self, paper: ResearchPaper) -> List[str]:
        # Use keyword extraction and clustering
        keywords = self._extract_keywords(paper.abstract)
        topics = self._cluster_keywords(keywords)
        return topics
```

### Enhanced Email Generation with Research Context
```python
# enhanced_email_generator.py
class EnhancedEmailGenerator(EmailGenerationService):
    async def generate_personalized_email(
        self,
        student_profile: StudentProfile,
        professor_profile: ResearchProfile,
        template: EmailTemplate
    ) -> GeneratedEmail:
        # Find research alignment
        alignment_score = self._calculate_alignment(
            student_profile.interests,
            professor_profile.research_topics
        )
        
        # Extract talking points from research papers
        talking_points = self._extract_talking_points(
            student_profile.skills,
            professor_profile.recent_papers
        )
        
        # Construct enhanced prompt
        prompt = self._construct_enhanced_prompt(
            template,
            student_profile,
            professor_profile,
            alignment_score,
            talking_points
        )
        
        # Generate email with enhanced context
        return await super().generate_email_with_prompt(prompt)
```

## Milestone 1.3: Email Optimization & A/B Testing

### A/B Testing Framework
```python
# ab_testing_service.py
class ABTestingService:
    def __init__(self, analytics_db):
        self.analytics_db = analytics_db
        self.experiments = {}
        
    async def create_experiment(
        self,
        name: str,
        variants: List[EmailVariant],
        metrics: List[str]
    ) -> Experiment:
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            variants=variants,
            metrics=metrics,
            status='active',
            created_at=datetime.utcnow()
        )
        
        # Initialize tracking
        await self._initialize_experiment_tracking(experiment)
        self.experiments[experiment.id] = experiment
        return experiment
    
    async def track_email_performance(
        self,
        experiment_id: str,
        variant_id: str,
        email_id: str,
        event: EmailEvent
    ):
        # Track opens, clicks, replies
        await self.analytics_db.insert_event({
            'experiment_id': experiment_id,
            'variant_id': variant_id,
            'email_id': email_id,
            'event_type': event.type,
            'timestamp': event.timestamp,
            'metadata': event.metadata
        })
        
    async def get_experiment_results(self, experiment_id: str) -> ExperimentResults:
        events = await self.analytics_db.get_events(experiment_id)
        
        # Calculate metrics
        results = ExperimentResults(experiment_id=experiment_id)
        for variant in self.experiments[experiment_id].variants:
            variant_events = [e for e in events if e.variant_id == variant.id]
            
            opens = len([e for e in variant_events if e.event_type == 'open'])
            replies = len([e for e in variant_events if e.event_type == 'reply'])
            total_sent = len([e for e in variant_events if e.event_type == 'sent'])
            
            results.add_variant_result(
                variant_id=variant.id,
                open_rate=opens / total_sent if total_sent > 0 else 0,
                reply_rate=replies / total_sent if total_sent > 0 else 0,
                sample_size=total_sent
            )
        
        return results
```

### Optimization ML Model
```python
# optimization_model.py
class EmailOptimizationModel:
    def __init__(self):
        self.model = self._initialize_model()
        self.feature_extractor = EmailFeatureExtractor()
        
    def train(self, training_data: List[EmailPerformance]):
        # Extract features from emails
        features = []
        labels = []
        
        for email_perf in training_data:
            features.append(self.feature_extractor.extract(email_perf.email))
            labels.append(email_perf.success_score)
        
        # Train model
        self.model.fit(features, labels)
        
    def predict_success(self, email: Email) -> float:
        features = self.feature_extractor.extract(email)
        return self.model.predict([features])[0]
    
    def suggest_improvements(self, email: Email) -> List[ImprovementSuggestion]:
        success_score = self.predict_success(email)
        
        if success_score < 0.7:
            # Generate improvement suggestions
            suggestions = self._analyze_email_weaknesses(email)
            return suggestions
        
        return []
```

## Infrastructure Requirements

### Services Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  email-generation:
    build: ./services/email-generation
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/torchmail
    ports:
      - "3001:3000"
    depends_on:
      - db
      - redis
  
  research-analyzer:
    build: ./services/research-analyzer
    environment:
      - ARXIV_API_KEY=${ARXIV_API_KEY}
      - GOOGLE_SCHOLAR_API_KEY=${GOOGLE_SCHOLAR_API_KEY}
    volumes:
      - ./models:/app/models
  
  ab-testing:
    build: ./services/ab-testing
    environment:
      - ANALYTICS_DB_URL=postgresql://user:pass@analytics-db:5432/analytics
    depends_on:
      - analytics-db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=torchmail
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  analytics-db:
    image: timescale/timescaledb:latest-pg15
    environment:
      - POSTGRES_DB=analytics
      - POSTGRES_USER=analytics_user
      - POSTGRES_PASSWORD=analytics_pass
```

### Monitoring & Observability
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'email-generation'
    static_configs:
      - targets: ['email-generation:3000']
    
  - job_name: 'research-analyzer'
    static_configs:
      - targets: ['research-analyzer:3000']
    
  - job_name: 'ab-testing'
    static_configs:
      - targets: ['ab-testing:3000']

# Custom metrics to track
# - email_generation_duration_seconds
# - email_generation_success_rate
# - research_analysis_duration_seconds
# - ab_test_conversion_rate
# - cache_hit_rate
```

## Security Considerations

### Data Protection
1. **PII Handling**: Student and professor data encrypted at rest and in transit
2. **API Security**: JWT tokens with short expiration, rate limiting
3. **AI Privacy**: Data anonymization before sending to external AI services
4. **Compliance**: GDPR, FERPA considerations for educational data

### Cost Management
1. **AI API Usage**: Caching, request batching, usage quotas
2. **Database Optimization**: Indexing, query optimization, connection pooling
3. **Infrastructure**: Auto-scaling based on demand, spot instances for batch jobs

## Testing Strategy

### Unit Tests
```python
# test_email_generation.py
def test_email_generation_basic():
    service = EmailGenerationService(api_key="test")
    template = EmailTemplate(name="Basic", content="Hello {name}")
    variables = {"name": "John"}
    
    email = service.generate_email(template, variables)
    assert "John" in email.content
    assert email.variables_used == variables

def test_research_analysis():
    analyzer = ResearchAnalyzer()
    profile = analyzer.analyze_research_papers("prof123")
    assert len(profile.papers) > 0
    assert profile.research_topics is not None
```

### Integration Tests
```python
# test_integration.py
async def test_end_to_end_email_generation():
    # Setup
    client = TestClient(app)
    
    # Create template
    template_resp = await client.post("/api/v1/templates", json={
        "name": "Test Template",
        "content": "Dear {professor}, I'm interested in {research_area}."
    })
    
    # Generate email
    email_resp = await client.post("/api/v1/emails/generate", json={
        "template_id": template_resp.json()["id"],
        "variables": {
            "professor": "Dr. Smith",
            "research_area": "AI Ethics"
        }
    })
    
    assert email_resp.status_code == 200
    assert "Dr. Smith" in email_resp.json()["content"]
```

### Performance Tests
```python
# test_performance.py
def test_email_generation_performance():
    service = EmailGenerationService(api_key="test")
    
    start_time = time.time()
    for _ in range(100):
        service.generate_email(template, variables)
    
    duration = time.time() - start_time
    assert duration < 10.0  # 100 emails in under 10 seconds
```

## Deployment Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy Email Generation Service

on:
  push:
    branches: [main]
    paths:
      - 'services/email-generation/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd services/email-generation
          npm test
          npm run lint
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          cd services/email-generation
          docker build -t torchmail/email-generation:${{ github.sha }} .
  
  deploy