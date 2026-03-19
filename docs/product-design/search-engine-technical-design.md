

## API Design

### Search API
```typescript
// POST /api/v1/search/labs
interface SearchRequest {
  query?: string;
  filters?: {
    university?: string[];
    department?: string[];
    research_area?: string[];
    hiring_status?: ('actively_hiring' | 'might_hire' | 'not_hiring')[];
    min_hiring_score?: number;
    lab_size?: {
      min?: number;
      max?: number;
    };
    location?: {
      latitude: number;
      longitude: number;
      radius_km: number;
    };
    application_deadline?: {
      before?: string; // ISO date
      after?: string; // ISO date
    };
  };
  sort_by?: 'relevance' | 'hiring_score' | 'compatibility' | 'recently_updated';
  page?: number;
  limit?: number;
  include_personalized?: boolean;
}

interface SearchResponse {
  total: number;
  page: number;
  limit: number;
  results: LabResult[];
  filters_available: AvailableFilters;
  query_time_ms: number;
  suggestions?: SearchSuggestion[];
}

interface LabResult {
  id: string;
  name: string;
  university: string;
  department: string;
  research_areas: string[];
  hiring_status: string;
  hiring_score: number;
  hiring_confidence: number;
  lab_size: number;
  location: {
    city: string;
    state: string;
    country: string;
    coordinates?: {
      lat: number;
      lon: number;
    };
  };
  compatibility_score?: number;
  match_explanation?: string;
  quick_actions: QuickAction[];
}

// GET /api/v1/search/suggestions?q=query
interface SuggestionResponse {
  queries: string[];
  filters: FilterSuggestion[];
  labs: LabSuggestion[];
}
```

### Recommendation API
```typescript
// GET /api/v1/recommendations
interface RecommendationRequest {
  student_profile_id: string;
  limit?: number;
  diversity_factor?: number; // 0-1, higher = more diverse recommendations
  include_explanations?: boolean;
  include_improvement_tips?: boolean;
}

interface RecommendationResponse {
  recommendations: Recommendation[];
  profile_completeness: number;
  skill_gaps: SkillGap[];
  timeline_suggestions: TimelineSuggestion[];
}

interface Recommendation {
  lab: LabResult;
  compatibility: {
    total: number;
    breakdown: {
      skills: number;
      research: number;
      timing: number;
      cultural: number;
    };
  };
  success_prediction: {
    interview_probability: number;
    acceptance_probability: number;
    expected_response_days: number;
  };
  action_plan: ActionStep[];
  priority: 'high' | 'medium' | 'low';
}
```

### Lab Profile API
```typescript
// GET /api/v1/labs/:id
interface LabProfileResponse {
  lab: DetailedLabProfile;
  hiring_timeline: HiringTimeline[];
  current_projects: ResearchProject[];
  team_members: TeamMember[];
  recent_publications: Publication[];
  application_process: ApplicationProcess;
  compatibility_analysis?: CompatibilityAnalysis;
  similar_labs: SimilarLab[];
}

interface DetailedLabProfile {
  id: string;
  name: string;
  professor: ProfessorInfo;
  university: UniversityInfo;
  research_focus: ResearchFocus[];
  lab_description: string;
  lab_culture: string;
  mentorship_style: string;
  funding_sources: string[];
  facilities: string[];
  hiring_status: HiringStatus;
  hiring_needs: HiringNeed[];
  application_deadlines: ApplicationDeadline[];
  contact_info: ContactInfo;
  social_links: SocialLink[];
  last_updated: string;
}

interface CompatibilityAnalysis {
  for_student?: string; // student ID if provided
  score: number;
  strengths: string[];
  areas_for_improvement: string[];
  suggested_preparation: PreparationStep[];
  competitive_landscape: CompetitiveAnalysis;
}
```

### Student Profile API
```typescript
// POST /api/v1/students/profiles
interface StudentProfileRequest {
  academic_level: 'undergraduate' | 'masters' | 'phd' | 'postdoc';
  gpa?: number;
  university: string;
  major: string;
  graduation_date: string;
  skills: Array<{
    name: string;
    level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    years_experience?: number;
  }>;
  research_interests: string[];
  previous_research: ResearchExperience[];
  career_goals: string[];
  availability: {
    start_date: string;
    end_date: string;
    hours_per_week: number;
  };
  preferences: {
    location_preferences: string[];
    lab_size_preference?: 'small' | 'medium' | 'large' | 'any';
    funding_requirement?: boolean;
    remote_possible?: boolean;
  };
}

interface StudentProfileResponse {
  profile_id: string;
  completeness_score: number;
  skill_analysis: SkillAnalysis;
  research_fit_analysis: ResearchFitAnalysis;
  timeline_analysis: TimelineAnalysis;
  improvement_recommendations: ImprovementRecommendation[];
  match_statistics: MatchStatistics;
}
```

## Data Pipeline Architecture

### Real-time Data Collection
```python
# data_pipeline.py
class DataPipeline:
    def __init__(self):
        self.collectors = {
            'web': WebDataCollector(),
            'api': APIDataCollector(),
            'social': SocialDataCollector(),
            'manual': ManualDataCollector()
        }
        self.processors = {
            'hiring': HiringIntentProcessor(),
            'profile': ProfileEnrichmentProcessor(),
            'temporal': TemporalAnalysisProcessor(),
            'quality': DataQualityProcessor()
        }
        self.storage = DataStorage()
        
    async def run_pipeline(self):
        """Run complete data pipeline"""
        while True:
            try:
                # 1. Collect data from all sources
                raw_data = await self._collect_data()
                
                # 2. Process and enrich data
                processed_data = await self._process_data(raw_data)
                
                # 3. Validate data quality
                validated_data = await self._validate_data(processed_data)
                
                # 4. Store in appropriate databases
                await self._store_data(validated_data)
                
                # 5. Update search indices
                await self._update_indices(validated_data)
                
                # 6. Generate analytics
                await self._generate_analytics(validated_data)
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_data(self):
        """Collect data from all sources in parallel"""
        tasks = []
        for name, collector in self.collectors.items():
            task = collector.collect()
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined = {}
        for name, result in zip(self.collectors.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Collector {name} failed: {result}")
            else:
                combined[name] = result
        
        return combined
```

### Search Index Update Service
```python
# index_updater.py
class IndexUpdater:
    def __init__(self, es_client, change_detector):
        self.es = es_client
        self.change_detector = change_detector
        
    async def update_index(self, lab_data: LabData):
        """Update search index with new lab data"""
        
        # Check if significant changes occurred
        changes = await self.change_detector.detect_changes(lab_data)
        
        if not changes.significant:
            # Only update timestamp
            await self.es.update(
                index='labs',
                id=lab_data.id,
                body={
                    'doc': {'last_updated': datetime.utcnow()}
                }
            )
            return
        
        # Prepare updated document
        doc = self._prepare_document(lab_data, changes)
        
        # Update index
        await self.es.index(
            index='labs',
            id=lab_data.id,
            body=doc,
            refresh='wait_for'
        )
        
        # Update related indices
        await self._update_related_indices(lab_data, changes)
        
        # Log update for analytics
        await self._log_update(lab_data, changes)
    
    def _prepare_document(self, lab_data: LabData, changes: ChangeSet):
        """Prepare Elasticsearch document with proper scoring"""
        doc = {
            'id': lab_data.id,
            'name': lab_data.name,
            'university': lab_data.university,
            'department': lab_data.department,
            'research_areas': lab_data.research_areas,
            'hiring_status': lab_data.hiring_status.value,
            'hiring_score': lab_data.hiring_score,
            'hiring_confidence': lab_data.hiring_confidence,
            'lab_size': lab_data.lab_size,
            'publication_count': len(lab_data.recent_publications),
            'grant_funding': lab_data.grant_funding,
            'skills_required': lab_data.skills_required,
            'application_deadline': lab_data.application_deadline,
            'location': {
                'lat': lab_data.location.lat,
                'lon': lab_data.location.lon
            },
            'embedding': lab_data.embedding,
            'last_updated': datetime.utcnow(),
            'boost_factor': self._calculate_boost(lab_data, changes)
        }
        
        # Add change flags for ranking
        if changes.hiring_status_changed:
            doc['recent_hiring_change'] = True
            doc['hiring_change_timestamp'] = changes.detected_at
        
        return doc
```

## Machine Learning Pipeline

### Feature Engineering Pipeline
```python
# feature_engineering.py
class FeatureEngineering:
    def __init__(self):
        self.text_features = TextFeatureExtractor()
        self.temporal_features = TemporalFeatureExtractor()
        self.structural_features = StructuralFeatureExtractor()
        
    async def extract_features(self, lab_data: LabData) -> Dict[str, Any]:
        """Extract features for ML models"""
        features = {}
        
        # Text-based features
        text_features = await self.text_features.extract(lab_data)
        features.update(text_features)
        
        # Temporal features
        temporal_features = await self.temporal_features.extract(lab_data)
        features.update(temporal_features)
        
        # Structural features
        structural_features = await self.structural_features.extract(lab_data)
        features.update(structural_features)
        
        # Derived features
        derived_features = self._create_derived_features(features)
        features.update(derived_features)
        
        return features
    
    def _create_derived_features(self, base_features: Dict) -> Dict:
        """Create derived/composite features"""
        derived = {}
        
        # Activity score
        if 'website_updates' in base_features and 'publication_count' in base_features:
            derived['activity_score'] = (
                base_features['website_updates'] * 0.3 +
                base_features['publication_count'] * 0.4 +
                base_features.get('social_activity', 0) * 0.3
            )
        
        # Hiring signal strength
        if 'hiring_keyword_count' in base_features:
            derived['hiring_signal_strength'] = (
                base_features['hiring_keyword_count'] /
                max(base_features.get('total_words', 1), 1)
            )
        
        return derived
```

### Model Training Pipeline
```python
# model_training.py
class ModelTrainingPipeline:
    def __init__(self, feature_store, model_registry):
        self.feature_store = feature_store
        self.model_registry = model_registry
        self.models = {
            'hiring_intent': HiringIntentModel(),
            'compatibility': CompatibilityModel(),
            'success_prediction': SuccessPredictionModel()
        }
        
    async def train_models(self):
        """Train all ML models with latest data"""
        
        # 1. Load training data
        training_data = await self.feature_store.get_training_data()
        
        # 2. Train each model
        for model_name, model in self.models.items():
            logger.info(f"Training {model_name} model...")
            
            # Prepare features and labels
            X, y = self._prepare_training_data(training_data, model_name)
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            metrics = model.evaluate(X_val, y_val)
            
            # Register model if improved
            if self._is_improvement(model_name, metrics):
                await self.model_registry.register(
                    model_name=model_name,
                    model=model,
                    metrics=metrics,
                    feature_importance=model.feature_importances_
                )
                
                logger.info(f"{model_name} model updated with metrics: {metrics}")
    
    def _prepare_training_data(self, data, model_name):
        """Prepare features and labels for specific model"""
        if model_name == 'hiring_intent':
            X = [d['features'] for d in data]
            y = [d['is_hiring'] for d in data]
        elif model_name == 'compatibility':
            X = [d['compatibility_features'] for d in data]
            y = [d['compatibility_score'] for d in data]
        elif model_name == 'success_prediction':
            X = [d['application_features'] for d in data]
            y = [d['success_outcome'] for d in data]
        
        return X, y
```

## Monitoring & Observability

### Search Performance Monitoring
```python
# search_monitor.py
class SearchMonitor:
    def __init__(self, metrics_client):
        self.metrics = metrics_client
        
    async def track_search(self, search_request: SearchRequest, response: SearchResponse):
        """Track search performance metrics"""
        
        # Latency metrics
        await self.metrics.timing(
            'search.latency',
            response.query_time_ms,
            tags={
                'query_length': len(search_request.query or ''),
                'filter_count': len(search_request.filters or {}),
                'result_count': len(response.results)
            }
        )
        
        # Quality metrics
        if search_request.include_personalized:
            compatibility_scores = [
                r.compatibility_score for r in response.results 
                if r.compatibility_score is not None
            ]
            if compatibility_scores:
                avg_compatibility = sum(compatibility_scores) / len(compatibility_scores)
                await self.metrics.gauge(
                    'search.avg_compatibility',
                    avg_compatibility
                )
        
        # User engagement metrics
        await self.metrics.increment(
            'search.requests',
            tags={'has_results': len(response.results) > 0}
        )
    
    async def track_clickthrough(self, search_id: str, lab_id: str, position: int):
        """Track clickthrough rates for search results"""
        await self.metrics.increment(
            'search.clickthrough',
            tags={
                'position': position,
                'position_group': self._get_position_group(position)
            }
        )
        
        # Calculate CTR for this position
        await self.metrics.gauge(
            'search.ctr_by_position',
            self._calculate_ctr(position),
            tags={'position': position}
        )
```

### Data Quality Monitoring
```python
# data_quality_monitor.py
class DataQualityMonitor:
    def __init__(self):
        self.checks = [
            CompletenessCheck(),
            AccuracyCheck(),
            FreshnessCheck(),
            ConsistencyCheck()
        ]
        
    async def run_quality_checks(self):
        """Run all data quality checks"""
        results = {}
        
        for check in self.checks:
            try:
                check_result = await check.run()
                results[check.name] = check_result
                
                # Alert if quality below threshold
                if check_result.score < check.threshold:
                    await self._send_alert(
                        f"Data quality alert: {check.name} score {check_result.score}",
                        check_result.details
                    )
                    
            except Exception as e:
                logger.error(f"Quality check {check.name} failed: {e}")
        
        # Store results for analytics
        await self._store_results(results)
        
        return results
    
    async def _send_alert(self, message: str, details: Dict):
        """Send data quality alert"""
        alert = {
            'severity': 'warning',
            'message': message,
            'details': details,
            'timestamp': datetime.utcnow()
        }
        
        # Send to monitoring system
        await self.metrics_client.send_alert(alert)
        
        # Log for debugging
        logger.warning(f"Data quality issue: {message}")
```

## Deployment & Scaling

### Kubernetes Deployment
```yaml
# search-engine-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-engine
  namespace: torchmail
spec:
  replicas: 3
  selector:
    matchLabels:
      app: search-engine
  template:
    metadata:
      labels:
        app: search-engine
    spec:
      containers:
      - name: search-api
        image: torchmail/search-engine:latest
        ports:
        - containerPort: 8080
        env:
        - name: ELASTICSEARCH_HOST
          value: "elasticsearch.torchmail.svc.cluster.local"
        - name: REDIS_HOST
          value: "redis.torchmail.svc.cluster.local"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
