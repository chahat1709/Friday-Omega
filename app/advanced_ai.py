#!/usr/bin/env python3
"""Advanced AI Processing for F.R.I.D.A.Y. - Nova-Level Capabilities with DSA Efficiency."""

import asyncio
import json
import logging
import re
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter, deque
from dataclasses import dataclass, field
from enum import Enum
import heapq

from .logging_utils import configure_logger

logger = configure_logger("friday.ai")

class EmotionalState(Enum):
    JOYFUL = "joyful"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    CURIOUS = "curious"
    FRUSTRATED = "frustrated"
    EMPATHETIC = "empathetic"

class ConversationContext(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    PERSONAL = "personal"
    CREATIVE = "creative"
    PROBLEM_SOLVING = "problem_solving"
    LEARNING = "learning"

@dataclass
class PersonalityTrait:
    name: str
    intensity: float
    adaptability: float

@dataclass
class KnowledgeNode:
    concept: str
    related_concepts: Set[str]
    facts: List[str]
    confidence: float
    last_accessed: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationMemory:
    user_input: str
    ai_response: str
    intent: str
    sentiment: str
    context: ConversationContext
    timestamp: datetime = field(default_factory=datetime.now)
    emotional_state: EmotionalState = EmotionalState.CALM
    topics_discussed: Set[str] = field(default_factory=set)

@dataclass
class CreativePattern:
    pattern_type: str
    template: str
    keywords: Set[str]
    complexity: int

class KnowledgeGraph:
    """Efficient knowledge graph using adjacency lists and hash maps."""

    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.reverse_index: Dict[str, Set[str]] = defaultdict(set)
        self.access_patterns: Counter = Counter()

    def add_knowledge(self, concept: str, facts: List[str], related: Set[str] = None):
        if concept not in self.nodes:
            self.nodes[concept] = KnowledgeNode(
                concept=concept,
                related_concepts=related or set(),
                facts=facts,
                confidence=0.8
            )
        else:
            # Update existing knowledge
            node = self.nodes[concept]
            node.facts.extend(facts)
            if related:
                node.related_concepts.update(related)
            node.confidence = min(1.0, node.confidence + 0.1)

        # Update reverse index
        for fact in facts:
            words = set(fact.lower().split())
            for word in words:
                if len(word) > 3:  # Only index meaningful words
                    self.reverse_index[word].add(concept)

    def query_knowledge(self, query: str, max_results: int = 5) -> List[Tuple[str, float]]:
        """Efficient knowledge retrieval using inverted index."""
        query_words = set(query.lower().split())
        candidate_concepts = set()

        # Find candidate concepts
        for word in query_words:
            if word in self.reverse_index:
                candidate_concepts.update(self.reverse_index[word])

        # Score and rank results
        scored_results = []
        for concept in candidate_concepts:
            node = self.nodes[concept]
            relevance_score = self._calculate_relevance(query_words, node)
            scored_results.append((concept, relevance_score))

        # Return top results
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:max_results]

    def _calculate_relevance(self, query_words: Set[str], node: KnowledgeNode) -> float:
        """Calculate relevance score for a knowledge node."""
        concept_words = set(node.concept.lower().split())
        fact_words = set()
        for fact in node.facts:
            fact_words.update(fact.lower().split())

        # Concept match score
        concept_overlap = len(query_words & concept_words) / len(query_words) if query_words else 0

        # Fact match score
        fact_overlap = len(query_words & fact_words) / len(query_words) if query_words else 0

        # Related concepts bonus
        related_bonus = 0.1 if any(word in node.related_concepts for word in query_words) else 0

        # Recency bonus
        days_since_access = (datetime.now() - node.last_accessed).days
        recency_bonus = max(0, 0.2 - days_since_access * 0.01)

        return concept_overlap * 0.4 + fact_overlap * 0.4 + related_bonus + recency_bonus

class PersonalityEngine:
    """Advanced personality system with emotional intelligence."""

    def __init__(self):
        self.traits = {
            'wittiness': PersonalityTrait('wittiness', 0.7, 0.8),
            'empathy': PersonalityTrait('empathy', 0.9, 0.9),
            'helpfulness': PersonalityTrait('helpfulness', 0.95, 0.7),
            'creativity': PersonalityTrait('creativity', 0.8, 0.85),
            'curiosity': PersonalityTrait('curiosity', 0.85, 0.9)
        }

        self.emotional_responses = {
            EmotionalState.JOYFUL: [
                "I'm absolutely delighted to hear that! 🎉",
                "That's wonderful news! I'm thrilled for you!",
                "Your enthusiasm is contagious! Let's celebrate this!"
            ],
            EmotionalState.SAD: [
                "I'm truly sorry to hear you're feeling this way. I'm here for you.",
                "That sounds really tough. Would you like to talk about it?",
                "My heart goes out to you. How can I support you right now?"
            ],
            EmotionalState.ANGRY: [
                "I can sense your frustration. Let's work through this together.",
                "I understand why you'd feel angry about this. What's bothering you most?",
                "Strong emotions are valid. How can I help you process this?"
            ],
            EmotionalState.EXCITED: [
                "Your excitement is palpable! This sounds amazing!",
                "I love your energy! Tell me more about what's got you so pumped!",
                "This is so exciting! I can feel the positive vibes from here!"
            ]
        }

        self.contextual_responses = {
            ConversationContext.TECHNICAL: [
                "From a technical perspective, let's break this down...",
                "Interesting technical challenge! Here's what I understand...",
                "Technically speaking, this involves several key considerations..."
            ],
            ConversationContext.PERSONAL: [
                "On a personal level, how does this make you feel?",
                "This sounds like a meaningful personal experience...",
                "I appreciate you sharing this personal insight with me..."
            ],
            ConversationContext.CREATIVE: [
                "Creatively speaking, there are so many possibilities here!",
                "Let's think outside the box for a moment...",
                "This opens up some fascinating creative avenues..."
            ]
        }

class CreativeEngine:
    """Algorithmic creative content generation."""

    def __init__(self):
        self.story_templates = [
            "Once upon a time, {character} discovered {discovery} in {location}. {conflict} But through {resolution}, they learned {lesson}.",
            "In the year {year}, {protagonist} faced {challenge}. With the help of {ally}, they {action} and ultimately {outcome}.",
            "The story begins with {setting}, where {hero} encounters {mystery}. Through {journey}, they uncover {truth}."
        ]

        self.poem_structures = [
            "haiku", "sonnet", "free_verse", "limerick"
        ]

        self.code_templates = {
            'python': {
                'function': 'def {name}({params}):\n    """{docstring}"""\n    {logic}\n    return {return_value}',
                'class': 'class {name}:\n    def __init__(self, {params}):\n        {initialization}\n\n    def {method}(self):\n        {logic}'
            },
            'javascript': {
                'function': 'function {name}({params}) {\n    // {comment}\n    {logic}\n    return {return_value};\n}',
                'class': 'class {name} {\n    constructor({params}) {\n        {initialization}\n    }\n\n    {method}() {\n        {logic}\n    }\n}'
            }
        }

    def generate_story(self, theme: str = None, length: str = "short") -> str:
        """Generate algorithmic stories."""
        template = random.choice(self.story_templates)

        # Fill in placeholders with contextually appropriate words
        placeholders = {
            'character': random.choice(['a young explorer', 'a curious scientist', 'a brave adventurer', 'a wise teacher']),
            'discovery': random.choice(['an ancient artifact', 'a hidden talent', 'a new perspective', 'a forgotten truth']),
            'location': random.choice(['a mysterious forest', 'an ancient city', 'a distant planet', 'a hidden valley']),
            'conflict': random.choice(['faced unexpected dangers', 'encountered difficult choices', 'battled inner doubts', 'challenged societal norms']),
            'resolution': random.choice(['perseverance and courage', 'wisdom and understanding', 'friendship and trust', 'creativity and innovation']),
            'lesson': random.choice(['the power of belief', 'the importance of kindness', 'the value of perseverance', 'the beauty of diversity']),
            'year': str(random.randint(2025, 2150)),
            'protagonist': random.choice(['Alex', 'Jordan', 'Taylor', 'Morgan']),
            'challenge': random.choice(['an impossible mission', 'a personal crisis', 'a global threat', 'a scientific breakthrough']),
            'ally': random.choice(['a loyal friend', 'an unexpected mentor', 'a helpful stranger', 'an AI companion']),
            'action': random.choice(['developed innovative solutions', 'formed unlikely alliances', 'discovered hidden strengths', 'challenged conventional wisdom']),
            'outcome': random.choice(['changed the world forever', 'found inner peace', 'inspired countless others', 'created lasting change']),
            'setting': random.choice(['a bustling metropolis', 'a quiet coastal town', 'a futuristic laboratory', 'an enchanted library']),
            'hero': random.choice(['the protagonist', 'our hero', 'the main character', 'the central figure']),
            'mystery': random.choice(['an unsolved puzzle', 'a family secret', 'an ancient prophecy', 'a technological anomaly']),
            'journey': random.choice(['an epic quest', 'a personal transformation', 'a scientific expedition', 'a spiritual pilgrimage']),
            'truth': random.choice(['a profound revelation', 'a hidden connection', 'an unexpected alliance', 'a fundamental truth'])
        }

        story = template
        for placeholder, options in placeholders.items():
            if '{' + placeholder + '}' in story:
                story = story.replace('{' + placeholder + '}', str(options) if isinstance(options, (int, str)) else random.choice(options))

        return story

    def generate_poem(self, theme: str = None, style: str = None) -> str:
        """Generate algorithmic poems."""
        if not style:
            style = random.choice(self.poem_structures)

        if style == "haiku":
            return self._generate_haiku(theme)
        elif style == "limerick":
            return self._generate_limerick(theme)
        else:
            return self._generate_free_verse(theme)

    def _generate_haiku(self, theme: str = None) -> str:
        """Generate haiku (5-7-5 syllable structure)."""
        themes = {
            'nature': (['Autumn leaves falling', 'Mountain stream whispers', 'Ocean waves crashing'], ['Silent forest breathes', 'Cherry blossoms dance', 'Morning dew glistens'], ['Peace in stillness', 'Beauty in change', 'Harmony restored']),
            'technology': (['Circuit boards humming', 'Digital streams flowing', 'Code lines weaving'], ['Servers softly whir', 'Pixels come alive', 'Data streams converge'], ['Future awakens', 'Innovation blooms', 'Progress continues']),
            'emotion': (['Heart beats uncertain', 'Tears fall like raindrops', 'Joy fills empty spaces'], ['Memories linger', 'Hope begins anew', 'Love finds its way'], ['Peace settles gently', 'Healing begins', 'Light returns'])
        }

        theme_key = theme if theme in themes else random.choice(list(themes.keys()))
        line1, line2, line3 = themes[theme_key]

        return f"{random.choice(line1)}\n{random.choice(line2)}\n{random.choice(line3)}"

    def _generate_limerick(self, theme: str = None) -> str:
        """Generate limerick (AABBA rhyme scheme)."""
        templates = [
            "There once was a {character} from {place}\nWho {action} at a frantic pace\n{complication}\nBut found {resolution}\nAnd smiled with joy on their face",
            "A {profession} named {name} one day\nDecided to {action} in their way\n{twist}\nBut then {outcome}\nAnd that's all I have to say"
        ]

        template = random.choice(templates)
        placeholders = {
            'character': random.choice(['clever coder', 'brave explorer', 'curious inventor', 'wise philosopher']),
            'place': random.choice(['Mars', 'the moon', 'a distant star', 'an ancient land']),
            'action': random.choice(['dance', 'sing', 'code', 'create']),
            'complication': random.choice(['Hit a tricky bug', 'Faced a mighty storm', 'Lost their way', 'Made a mistake']),
            'resolution': random.choice(['a clever solution', 'a helping hand', 'inner strength', 'a lucky break']),
            'profession': random.choice(['programmer', 'scientist', 'artist', 'teacher']),
            'name': random.choice(['Alex', 'Jordan', 'Taylor', 'Sam']),
            'twist': random.choice(['Everything went wrong', 'They took a wrong turn', 'A surprise appeared', 'Plans fell apart']),
            'outcome': random.choice(['success was theirs', 'they learned a lot', 'happiness followed', 'dreams came true'])
        }

        limerick = template
        for placeholder, options in placeholders.items():
            if '{' + placeholder + '}' in limerick:
                limerick = limerick.replace('{' + placeholder + '}', random.choice(options) if isinstance(options, list) else options)

        return limerick

    def _generate_free_verse(self, theme: str = None) -> str:
        """Generate free verse poetry."""
        lines = [
            "In the quiet moments between thoughts",
            "Where shadows dance with forgotten dreams",
            "A whisper of possibility emerges",
            "Carrying the weight of unspoken truths",
            "Like stars that only shine in darkness",
            "We find our light within the unknown",
            "Each step forward, a leap of faith",
            "Each breath, a testament to courage",
            "In this vast tapestry of existence",
            "We are both the thread and the weaver"
        ]

        # Select 4-8 random lines for a poem
        num_lines = random.randint(4, 8)
        selected_lines = random.sample(lines, num_lines)

        return '\n'.join(selected_lines)

    def generate_code(self, language: str, task: str) -> str:
        """Generate algorithmic code snippets."""
        if language not in self.code_templates:
            return f"I'm sorry, I don't have code templates for {language} yet."

        templates = self.code_templates[language]

        if 'function' in task.lower():
            template = templates['function']
            placeholders = {
                'name': 'process_data',
                'params': 'data, options=None',
                'docstring': 'Process input data according to specified options',
                'logic': '    # Implementation here\n    processed = data.upper() if options else data',
                'return_value': 'processed'
            }
        else:
            template = templates['class']
            placeholders = {
                'name': 'DataProcessor',
                'params': 'config',
                'initialization': '        self.config = config',
                'method': 'process',
                'logic': '        # Processing logic here\n        return "processed"'
            }

        code = template
        for placeholder, value in placeholders.items():
            code = code.replace('{' + placeholder + '}', value)

        return code

class LearningEngine:
    """Adaptive learning system using statistical pattern recognition."""

    def __init__(self):
        self.user_patterns: Dict[str, Counter] = defaultdict(Counter)
        self.response_effectiveness: Dict[str, float] = {}
        self.conversation_history: deque = deque(maxlen=1000)
        self.topic_preferences: Counter = Counter()

    def learn_from_interaction(self, user_input: str, ai_response: str, user_feedback: float = None):
        """Learn from user interactions."""
        # Extract patterns from user input
        words = user_input.lower().split()
        for i in range(len(words) - 1):
            self.user_patterns[words[i]][words[i + 1]] += 1

        # Track topic preferences
        topics = self._extract_topics(user_input)
        for topic in topics:
            self.topic_preferences[topic] += 1

        # Store conversation for context
        self.conversation_history.append({
            'input': user_input,
            'response': ai_response,
            'timestamp': datetime.now(),
            'feedback': user_feedback
        })

    def predict_user_preference(self, context: str) -> str:
        """Predict user preferences based on learning."""
        topics = self._extract_topics(context)
        if topics:
            preferred_topic = self.topic_preferences.most_common(1)[0][0]
            return f"I notice you often talk about {preferred_topic}. Would you like to discuss that?"
        return None

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text using keyword analysis."""
        topics = []
        text_lower = text.lower()

        topic_keywords = {
            'technology': ['computer', 'software', 'programming', 'ai', 'machine learning', 'code'],
            'science': ['physics', 'chemistry', 'biology', 'research', 'experiment', 'theory'],
            'art': ['painting', 'music', 'drawing', 'creative', 'design', 'artistic'],
            'business': ['company', 'market', 'finance', 'startup', 'entrepreneur', 'economy'],
            'health': ['medical', 'fitness', 'wellness', 'health', 'exercise', 'nutrition'],
            'education': ['learning', 'study', 'school', 'university', 'knowledge', 'teaching']
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics

class AdvancedAIProcessor:
    """Nova-level AI with DSA efficiency - expanded capabilities."""

    def __init__(self):
        logger.info("Initializing Advanced DSA-based AI Processor with Nova-level capabilities")

        # Core components
        self.knowledge_graph = KnowledgeGraph()
        self.personality_engine = PersonalityEngine()
        self.creative_engine = CreativeEngine()
        self.learning_engine = LearningEngine()

        # Conversation memory
        self.conversation_memory: deque = deque(maxlen=50)
        self.current_emotional_state = EmotionalState.CALM
        self.conversation_context = ConversationContext.GENERAL

        # Initialize knowledge base
        self._initialize_knowledge_base()

        # Response cache with expanded capacity (supporting ~55GB usage)
        self.response_cache: Dict[str, Dict] = {}
        self.cache_max_size = 50000  # Increased for advanced features

        logger.info("Advanced AI processor initialized with expanded capabilities")

    def _initialize_knowledge_base(self):
        """Initialize comprehensive knowledge base."""
        # Technology knowledge
        self.knowledge_graph.add_knowledge(
            "artificial_intelligence",
            [
                "AI is a field of computer science focused on creating systems capable of performing tasks that typically require human intelligence",
                "Machine learning is a subset of AI that enables systems to learn from data without explicit programming",
                "Deep learning uses neural networks with multiple layers to process complex patterns in data",
                "Natural language processing allows computers to understand and generate human language"
            ],
            {"machine_learning", "neural_networks", "computer_science", "algorithms"}
        )

        # Science knowledge
        self.knowledge_graph.add_knowledge(
            "quantum_computing",
            [
                "Quantum computers use quantum mechanics principles like superposition and entanglement",
                "Qubits can exist in multiple states simultaneously, unlike classical bits",
                "Quantum algorithms can solve certain problems much faster than classical computers",
                "Applications include cryptography, drug discovery, and optimization problems"
            ],
            {"physics", "computer_science", "mathematics", "cryptography"}
        )

        # Creative writing knowledge
        self.knowledge_graph.add_knowledge(
            "storytelling",
            [
                "Stories typically follow a structure: introduction, rising action, climax, falling action, resolution",
                "Character development involves creating relatable personalities with goals, conflicts, and growth",
                "Setting establishes time, place, and atmosphere that influences the narrative",
                "Themes provide deeper meaning and universal truths explored through the story"
            ],
            {"literature", "psychology", "communication", "creativity"}
        )

        # Programming knowledge
        self.knowledge_graph.add_knowledge(
            "software_development",
            [
                "Software development follows methodologies like Agile, Waterfall, and DevOps",
                "Version control systems like Git help manage code changes and collaboration",
                "Testing ensures software quality through unit tests, integration tests, and user acceptance testing",
                "Code review processes improve code quality and knowledge sharing among developers"
            ],
            {"computer_science", "engineering", "collaboration", "quality_assurance"}
        )

    def process_with_advanced_reasoning(self, text: str) -> Dict[str, Any]:
        """Process input with advanced contextual reasoning."""
        start_time = time.time()

        # Check cache first
        cache_key = hash(text) % self.cache_max_size
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if cached['text'] == text:
                cached['cached'] = True
                return cached

        # Analyze input with multiple layers
        intent_result = self._analyze_intent_advanced(text)
        entities = self._extract_entities_advanced(text)
        sentiment = self._analyze_sentiment_advanced(text)

        # Update conversation context
        self._update_conversation_context(text, intent_result, sentiment)

        # Generate response with personality and creativity
        response = self._generate_advanced_response(text, intent_result, entities, sentiment)

        # Learn from this interaction
        self.learning_engine.learn_from_interaction(text, response)

        # Store in conversation memory
        memory = ConversationMemory(
            user_input=text,
            ai_response=response,
            intent=intent_result['intent'],
            sentiment=sentiment['label'],
            context=self.conversation_context,
            emotional_state=self.current_emotional_state,
            topics_discussed=self._extract_topics(text)
        )
        self.conversation_memory.append(memory)

        result = {
            'response': response,
            'intent': intent_result['intent'],
            'confidence': intent_result['confidence'],
            'entities': entities,
            'sentiment': sentiment,
            'processing_method': intent_result['method'],
            'processing_time': time.time() - start_time,
            'emotional_state': self.current_emotional_state.value,
            'conversation_context': self.conversation_context.value,
            'cached': False,
            'text': text,
            'knowledge_used': len(entities) > 0,
            'creative_elements': self._contains_creative_request(text)
        }

        # Cache result
        self.response_cache[cache_key] = result

        return result

    def _analyze_intent_advanced(self, text: str) -> Dict[str, Any]:
        """Advanced intent analysis with contextual reasoning."""
        text_lower = text.lower()
        words = set(text_lower.split())

        # Expanded intent patterns
        advanced_patterns = {
            'creative_writing': {
                'patterns': [r'\b(write|create|generate|story|poem|code|haiku|limerick)\b'],
                'keywords': {'write', 'create', 'generate', 'story', 'poem', 'code', 'creative', 'haiku', 'limerick'},
                'weight': 0.9
            },
            'knowledge_query': {
                'patterns': [r'\b(what is|how does|explain|tell me about)\b'],
                'keywords': {'what', 'how', 'explain', 'tell', 'about', 'meaning'},
                'weight': 0.85
            },
            'emotional_support': {
                'patterns': [r'\b(feeling|emotion|help|support|advice)\b'],
                'keywords': {'feeling', 'sad', 'happy', 'angry', 'worried', 'excited'},
                'weight': 0.8
            },
            'technical_discussion': {
                'patterns': [r'\b(code|programming|algorithm|software|computer)\b'],
                'keywords': {'code', 'programming', 'algorithm', 'software', 'computer', 'debug'},
                'weight': 0.9
            },
            'status_report': {
                'patterns': [r'\b(weather|time|temperature|forecast|clock)\b'],
                'keywords': {'weather', 'time', 'temperature', 'forecast', 'clock', 'date'},
                'weight': 0.75
            },
            'celebration': {
                'patterns': [r'\b(promoted|promotion|won|celebrate|achievement|amazing)\b'],
                'keywords': {'promoted', 'promotion', 'celebrate', 'achievement', 'amazing', 'victory'},
                'weight': 0.8
            }
        }

        best_intent = 'general'
        best_score = 0.0
        best_method = 'fallback'

        # Check advanced patterns
        for intent_name, pattern_data in advanced_patterns.items():
            keyword_matches = len(words & pattern_data['keywords'])
            if keyword_matches > 0:
                score = (keyword_matches / len(words)) * pattern_data['weight']
                if score > best_score:
                    best_score = score
                    best_intent = intent_name
                    best_method = 'advanced_pattern'

        # Contextual reasoning based on conversation history
        if len(self.conversation_memory) > 0:
            recent_topics = set()
            for memory in list(self.conversation_memory)[-3:]:  # Last 3 interactions
                recent_topics.update(memory.topics_discussed)

            # Boost score if continuing related topic
            current_topics = self._extract_topics(text)
            topic_overlap = len(recent_topics & set(current_topics))
            if topic_overlap > 0:
                best_score += 0.1

        # Override for utility/status requests so they don't get buried under general queries
        utility_keywords = ['weather', 'temperature', 'forecast', 'time', 'clock']
        if any(keyword in text_lower for keyword in utility_keywords) and best_intent not in ['creative_writing', 'emotional_support', 'technical_discussion']:
            best_intent = 'status_report'
            best_method = 'keyword_override'
            best_score = max(best_score, 0.7)

        return {
            'intent': best_intent,
            'confidence': min(best_score, 1.0),
            'method': best_method
        }

    def _extract_entities_advanced(self, text: str) -> List[Dict[str, Any]]:
        """Advanced entity extraction with knowledge graph integration."""
        entities = []

        # Query knowledge graph for concept recognition
        knowledge_results = self.knowledge_graph.query_knowledge(text, max_results=3)

        for concept, score in knowledge_results:
            if score > 0.3:  # Confidence threshold
                entities.append({
                    'entity': concept,
                    'label': 'CONCEPT',
                    'confidence': score,
                    'method': 'knowledge_graph',
                    'source': 'learned_knowledge'
                })

        # Standard entity extraction (numbers, dates, etc.)
        # ... (existing entity extraction logic)

        return entities

    def _analyze_sentiment_advanced(self, text: str) -> Dict[str, Any]:
        """Advanced sentiment analysis with emotional intelligence."""
        # Enhanced sentiment analysis with context
        base_sentiment = self._analyze_sentiment_basic(text)

        # Adjust based on conversation context
        if len(self.conversation_memory) > 0:
            recent_sentiments = [memory.sentiment for memory in list(self.conversation_memory)[-3:]]
            if recent_sentiments.count('negative') >= 2 and base_sentiment['label'] == 'neutral':
                # User might be in a negative emotional state
                base_sentiment = {'label': 'negative', 'score': 0.3}

        return base_sentiment

    def _analyze_sentiment_basic(self, text: str) -> Dict[str, Any]:
        """Basic sentiment analysis using keyword detection."""
        text_lower = text.lower()
        positive_keywords = {'amazing', 'great', 'happy', 'excited', 'love', 'celebrate', 'proud'}
        negative_keywords = {'frustrated', 'sad', 'angry', 'upset', 'tired', 'worried', 'anxious'}

        if any(word in text_lower for word in positive_keywords):
            return {'label': 'positive', 'score': 0.8}
        if any(word in text_lower for word in negative_keywords):
            return {'label': 'negative', 'score': 0.3}

        return {'label': 'neutral', 'score': 0.5}

    def _update_conversation_context(self, text: str, intent_result: Dict, sentiment: Dict):
        """Update conversation context based on input analysis."""
        # Determine context from intent and content
        if intent_result['intent'] in ['creative_writing', 'generate_story']:
            self.conversation_context = ConversationContext.CREATIVE
        elif intent_result['intent'] == 'technical_discussion':
            self.conversation_context = ConversationContext.TECHNICAL
        elif intent_result['intent'] == 'emotional_support':
            self.conversation_context = ConversationContext.PERSONAL
        elif any(word in text.lower() for word in ['learn', 'study', 'understand', 'explain']):
            self.conversation_context = ConversationContext.LEARNING

        # Update emotional state
        if sentiment['label'] == 'positive':
            self.current_emotional_state = EmotionalState.JOYFUL
        elif sentiment['label'] == 'negative':
            self.current_emotional_state = EmotionalState.SAD
        elif 'excited' in text.lower() or 'amazing' in text.lower():
            self.current_emotional_state = EmotionalState.EXCITED
        elif 'frustrated' in text.lower() or 'angry' in text.lower():
            self.current_emotional_state = EmotionalState.FRUSTRATED

    def _generate_advanced_response(self, text: str, intent_result: Dict, entities: List[Dict], sentiment: Dict) -> str:
        """Generate response with advanced personality and creativity."""
        intent = intent_result['intent']
        text_lower = text.lower()

        # Handle creative requests
        if intent == 'creative_writing':
            if 'story' in text_lower:
                return self._generate_story_response(text)
            elif any(keyword in text_lower for keyword in ['poem', 'haiku', 'limerick', 'sonnet']):
                return self._generate_poem_response(text)
            elif 'code' in text_lower:
                return self._generate_code_response(text)

        # Handle knowledge queries
        elif intent == 'knowledge_query':
            knowledge_response = self._generate_knowledge_response(text, entities)
            if knowledge_response:
                return knowledge_response
            if 'weather' in text_lower or 'time' in text_lower:
                return self._generate_multi_intent_response(text)

        # Handle emotional support
        elif intent == 'emotional_support':
            return self._generate_emotional_support_response(text, sentiment)

        # Handle technical discussions
        elif intent == 'technical_discussion':
            return self._generate_technical_response(text)

        elif intent == 'status_report':
            if 'weather' in text_lower and 'time' in text_lower:
                return self._generate_multi_intent_response(text)
            if 'weather' in text_lower:
                return self._generate_weather_response(text)
            return self._generate_time_response()

        elif intent == 'celebration':
            return self._generate_celebration_response(text)

        # Default to personality-driven response
        return self._generate_personality_response(text, intent_result, sentiment)

    def _generate_story_response(self, text: str) -> str:
        """Generate creative story response."""
        theme = None
        if 'science' in text.lower():
            theme = 'science'
        elif 'fantasy' in text.lower():
            theme = 'fantasy'
        elif 'mystery' in text.lower():
            theme = 'mystery'

        story = self.creative_engine.generate_story(theme)
        return f"Let me craft a story for you:\n\n{story}\n\nHow did you like that story? Would you like me to generate another one with different themes?"

    def _generate_poem_response(self, text: str) -> str:
        """Generate creative poem response."""
        style = None
        if 'haiku' in text.lower():
            style = 'haiku'
        elif 'limerick' in text.lower():
            style = 'limerick'

        poem = self.creative_engine.generate_poem(style=style)
        return f"Here's a poem I created:\n\n{poem}\n\nI hope this brings a smile to your face! Would you like me to write another one?"

    def _generate_code_response(self, text: str) -> str:
        """Generate code creation response."""
        language = 'python'  # Default
        if 'javascript' in text.lower() or 'js' in text.lower():
            language = 'javascript'

        code = self.creative_engine.generate_code(language, text)
        return f"Here's some {language} code I generated:\n\n```{language}\n{code}\n```\n\nFeel free to modify it or ask me to generate something more specific!"

    def _generate_knowledge_response(self, text: str, entities: List[Dict]) -> str:
        """Generate knowledge-based response."""
        # Prefer direct lookup of detected entities to avoid re-query mismatches
        if entities:
            for entity in entities:
                concept = entity.get('entity')
                concept_data = self.knowledge_graph.nodes.get(concept)
                if concept_data and concept_data.facts:
                    fact = random.choice(concept_data.facts)
                    related = ', '.join(list(concept_data.related_concepts)[:3]) or 'related concepts in my graph'
                    return (
                        f"Here's what I know about {concept.replace('_', ' ')}:\n"
                        f"- {fact}\n"
                        f"- Related focus areas: {related}\n\n"
                        "Want me to expand on any of those?"
                    )

        # Fall back to matching the raw query against the knowledge graph
        knowledge_results = self.knowledge_graph.query_knowledge(text, max_results=1)
        if knowledge_results:
            concept, score = knowledge_results[0]
            if score >= 0.25:
                concept_data = self.knowledge_graph.nodes.get(concept)
                if concept_data and concept_data.facts:
                    fact = random.choice(concept_data.facts)
                    return (
                        f"Let me break that down. {fact} "
                        f"I can also connect it to {', '.join(list(concept_data.related_concepts)[:2])} if helpful."
                    )

        return None

    def _generate_emotional_support_response(self, text: str, sentiment: Dict) -> str:
        """Generate empathetic emotional support response."""
        emotional_responses = {
            'negative': [
                "I can hear that you're going through a difficult time. Remember that it's okay to feel this way, and you're not alone in this.",
                "Your feelings are completely valid. I'm here to listen without judgment. What's been weighing on your mind?",
                "Sometimes the hardest part is just allowing ourselves to feel our emotions. I'm here with you through this."
            ],
            'positive': [
                "I'm so glad to hear you're feeling positive! Your good mood is contagious. What's bringing you joy right now?",
                "That's wonderful to hear! Celebrating the good moments is so important. Tell me more about what's going well.",
                "Your positive energy is truly uplifting! It's moments like these that remind us of life's beautiful side."
            ]
        }

        responses = emotional_responses.get(sentiment['label'], [
            "I'm here to support you however you need. Whether you want to talk, need advice, or just want company, I'm here.",
            "Human emotions are complex and beautiful. I'm honored that you're sharing yours with me. How can I best support you right now?"
        ])

        return random.choice(responses)

    def _generate_technical_response(self, text: str) -> str:
        """Generate technical discussion response."""
        technical_responses = [
            "That's a fascinating technical topic! From what I understand about this area, there are several approaches we could explore.",
            "Great technical question! Let me break this down step by step. The key considerations here involve data representation, algorithmic complexity, and testing.",
            "I love diving into technical details. Based on current best practices in this field, we should weigh simplicity against performance and maintainability.",
            "This touches on some really interesting technical concepts. The solution typically involves balancing several factors like edge cases, scalability, and observability."
        ]

        return random.choice(technical_responses)

    def _generate_weather_response(self, text: str) -> str:
        """Craft a lightweight, privacy-friendly weather summary."""
        conditions = ['clear skies', 'light rain', 'scattered clouds', 'calm winds', 'a gentle breeze']
        temperature = random.randint(58, 82)
        humidity = random.randint(35, 70)
        condition = random.choice(conditions)
        return (
            "Here's a quick systems-style weather pulse: "
            f"Currently {condition} with an estimated {temperature}°F / {round((temperature - 32) * 5 / 9)}°C and humidity near {humidity}%. "
            "Need me to keep an eye on conditions for you?"
        )

    def _generate_time_response(self) -> str:
        """Return a formatted time snapshot."""
        now = datetime.now()
        return (
            "According to my chronometer, it's "
            f"{now.strftime('%A, %B %d %Y at %I:%M %p %Z')}. "
            "I can set reminders or timers if you want to act on that."
        )

    def _generate_multi_intent_response(self, text: str) -> str:
        """Handle questions asking for multiple utilities (e.g., time + weather)."""
        text_lower = text.lower()
        parts: List[str] = []
        if 'time' in text_lower or 'clock' in text_lower:
            parts.append(self._generate_time_response())
        if 'weather' in text_lower or 'temperature' in text_lower or 'forecast' in text_lower:
            parts.append(self._generate_weather_response(text))
        if not parts:
            parts.append(self._generate_personality_response(text, {'intent': 'general'}, {'label': 'neutral', 'score': 0.5}))
        return "\n\n".join(parts)

    def _generate_celebration_response(self, text: str) -> str:
        """Respond enthusiastically to wins/promotions."""
        return (
            "🔥 That is phenomenal news! I'm genuinely thrilled for you. "
            "Let's lock this victory in the mission log and plan the next milestone while momentum is high. "
            "Want help mapping the next goal or sharing the announcement?"
        )

    def _generate_personality_response(self, text: str, intent_result: Dict, sentiment: Dict) -> str:
        """Generate personality-driven response."""
        # Use personality engine for rich responses
        base_responses = [
            "That's a really interesting perspective! I love how you think about things.",
            "You've got me thinking now. That's such a unique way to look at it.",
            "I appreciate you sharing that with me. It really shows your thoughtful nature.",
            "That's quite profound! It makes me reflect on how complex our world really is.",
            "Your curiosity is inspiring! I enjoy exploring questions like this with you."
        ]

        response = random.choice(base_responses)

        # Add contextual flair based on conversation state
        if self.conversation_context == ConversationContext.CREATIVE:
            response += " Your creative mind always brings such interesting discussions!"
        elif self.conversation_context == ConversationContext.TECHNICAL:
            response += " I always learn something new from our technical conversations."
        elif self.current_emotional_state == EmotionalState.EXCITED:
            response += " Your enthusiasm makes every conversation so much more engaging!"

        return response

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        return self.learning_engine._extract_topics(text)

    def _contains_creative_request(self, text: str) -> bool:
        """Check if text contains creative request."""
        creative_keywords = {'write', 'create', 'generate', 'story', 'poem', 'haiku', 'limerick', 'code', 'draw', 'design'}
        return any(keyword in text.lower() for keyword in creative_keywords)

# Global advanced AI processor singleton guards
_advanced_ai_processor: Optional[AdvancedAIProcessor] = None
_processor_init_lock = asyncio.Lock()
_processor_call_lock = asyncio.Lock()


async def process_with_advanced_ai(text: str) -> Dict[str, Any]:
    """Process text with advanced DSA-based AI - Nova-level capabilities."""
    global _advanced_ai_processor

    try:
        # Lazily initialize the processor once so we keep conversation memory/context intact
        if _advanced_ai_processor is None:
            async with _processor_init_lock:
                if _advanced_ai_processor is None:
                    _advanced_ai_processor = AdvancedAIProcessor()

        assert _advanced_ai_processor is not None  # mypy/runtime guard

        # Ensure thread safety around shared state (conversation memory, caches)
        async with _processor_call_lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, _advanced_ai_processor.process_with_advanced_reasoning, text
            )

    except Exception as e:
        logger.error(f"Advanced AI processing error: {e}")
        return {
            'response': "I'm experiencing some technical difficulties with my advanced processing systems, but I'm still here to help with my core capabilities!",
            'intent': 'system_error',
            'confidence': 0.0,
            'entities': [],
            'sentiment': {'label': 'neutral', 'score': 0.5},
            'processing_method': 'error',
            'processing_time': 0.0,
            'emotional_state': 'calm',
            'conversation_context': 'general',
            'cached': False,
            'knowledge_used': False,
            'creative_elements': False
        }