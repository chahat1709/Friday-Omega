/**
 * Emotion Engine - Maps computed emotions to response formatting, tone, and personality
 * Integrates sentiment, user state, conversation history to drive conditional responses
 */

const emotionLevels = {
  VERY_POSITIVE: { emoji: '😄', color: '#00FF00', tone: 'energetic', intensity: 1.0 },
  POSITIVE: { emoji: '🙂', color: '#00DD00', tone: 'friendly', intensity: 0.7 },
  NEUTRAL: { emoji: '😐', color: '#00BB00', tone: 'professional', intensity: 0.5 },
  SLIGHTLY_NEGATIVE: { emoji: '😕', color: '#FFAA00', tone: 'concerned', intensity: 0.4 },
  NEGATIVE: { emoji: '😞', color: '#FF6600', tone: 'apologetic', intensity: 0.2 },
  VERY_NEGATIVE: { emoji: '😠', color: '#FF0000', tone: 'urgent', intensity: 0.0 }
};

const toneMappings = {
  energetic: {
    prefixes: ['Absolutely! ', 'Let\'s go! ', 'Right away! ', 'No problem! '],
    suffixes: [' 🚀', ' Let\'s do this!', ' Ready to help!'],
    style: 'enthusiastic'
  },
  friendly: {
    prefixes: ['Sure thing! ', 'Of course! ', 'Happy to help! ', 'Glad you asked! '],
    suffixes: [' 😊', ' Hope this helps!', ' Feel free to ask more!'],
    style: 'warm'
  },
  professional: {
    prefixes: ['Based on the data: ', 'Here\'s what I found: ', 'In summary: ', 'To address your query: '],
    suffixes: [' Let me know if you need clarification.', ' Does that answer your question?'],
    style: 'technical'
  },
  concerned: {
    prefixes: ['I understand your concern. ', 'Let me help clarify. ', 'That\'s important. ', 'I see the issue. '],
    suffixes: [' Let me look into this further.', ' I\'m here to help resolve this.'],
    style: 'supportive'
  },
  apologetic: {
    prefixes: ['I apologize, ', 'Unfortunately, ', 'I\'m sorry, ', 'That\'s challenging: '],
    suffixes: [' I\'m working on this.', ' Please bear with me.', ' Let\'s find a solution.'],
    style: 'understanding'
  },
  urgent: {
    prefixes: ['CRITICAL: ', 'IMMEDIATE ACTION: ', 'ALERT: ', 'PRIORITY: '],
    suffixes: [' This needs attention NOW!', ' Take action immediately!'],
    style: 'high-priority'
  },
  brotherly: {
    prefixes: ['Hey man, ', 'Look, ', 'Buddy, ', 'Real talk: ', 'Honestly, '],
    suffixes: [' We got this, bro.', ' No worries, I\'m here.', ' You got me?', ' We\'ll figure it out together.', ' Trust me on this.'],
    style: 'supportive-casual'
  }
};

class EmotionEngine {
  constructor() {
    this.userMood = 'NEUTRAL';
    this.conversationHistory = [];
    this.emotionalMemory = {};
    this.responseCount = 0;
  }

  /**
   * Classify emotion based on sentiment score and context
   */
  classifyEmotion(sentimentScore, context = {}) {
    // Sentiment score: -1 (very negative) to +1 (very positive)
    if (sentimentScore >= 0.7) return 'VERY_POSITIVE';
    if (sentimentScore >= 0.4) return 'POSITIVE';
    if (sentimentScore > -0.4) return 'NEUTRAL';
    if (sentimentScore > -0.7) return 'SLIGHTLY_NEGATIVE';
    if (sentimentScore > -0.9) return 'NEGATIVE';
    return 'VERY_NEGATIVE';
  }

  /**
   * Update user mood based on conversation pattern
   */
  updateUserMood(messageText, sentimentScore) {
    const currentEmotion = this.classifyEmotion(sentimentScore);
    
    // Track mood shift
    if (this.conversationHistory.length > 0) {
      const lastEmotion = this.conversationHistory[this.conversationHistory.length - 1].emotion;
      this.emotionalMemory[`transition_${lastEmotion}_to_${currentEmotion}`] = 
        (this.emotionalMemory[`transition_${lastEmotion}_to_${currentEmotion}`] || 0) + 1;
    }

    this.conversationHistory.push({
      timestamp: Date.now(),
      text: messageText,
      emotion: currentEmotion,
      sentiment: sentimentScore
    });

    // Keep only last 50 messages
    if (this.conversationHistory.length > 50) {
      this.conversationHistory.shift();
    }

    this.userMood = currentEmotion;
    return currentEmotion;
  }

  /**
   * Determine AI emotional response based on user mood and conversation context
   */
  getAIEmotion(userEmotion, conversationTopic = 'general') {
    // AI responds empathetically or energetically based on user state
    if (userEmotion === 'VERY_NEGATIVE' || userEmotion === 'NEGATIVE') {
      return 'brotherly'; // AI becomes supportive and friendly like a brother
    }
    if (userEmotion === 'VERY_POSITIVE') {
      return 'energetic'; // AI matches user's energy
    }
    if (conversationTopic === 'urgent' || conversationTopic === 'critical') {
      return 'urgent'; // AI is alert and focused
    }
    return 'brotherly'; // Default to brotherly tone (warm, supportive, casual)
  }

  /**
   * Format response with emotion expression
   */
  formatResponseWithEmotion(baseResponse, userEmotion, aiTone = null) {
    const emotion = emotionLevels[userEmotion] || emotionLevels.NEUTRAL;
    const tone = aiTone || this.getAIEmotion(userEmotion);
    const toneConfig = toneMappings[tone] || toneMappings.professional;

    // Add prefix and suffix based on tone
    let prefix = toneConfig.prefixes[Math.floor(Math.random() * toneConfig.prefixes.length)];
    let suffix = toneConfig.suffixes[Math.floor(Math.random() * toneConfig.suffixes.length)];

    // Truncate response if too long and energetic
    let formattedResponse = baseResponse;
    if (tone === 'energetic' && baseResponse.length > 500) {
      formattedResponse = baseResponse.substring(0, 500) + '...';
    }

    // Add emoji prefix
    const emotionEmoji = emotion.emoji;

    return {
      text: `${emotionEmoji} ${prefix}${formattedResponse}${suffix}`,
      emotion: userEmotion,
      tone: tone,
      color: emotion.color,
      intensity: emotion.intensity
    };
  }

  /**
   * Generate conditional response based on conversation state machine
   */
  generateConditionalResponse(baseResponse, context = {}) {
    const {
      userEmotion = this.userMood,
      topic = 'general',
      messageLength = baseResponse.length,
      isRepeat = false,
      userFrustration = 0
    } = context;

    // State machine: decide response strategy
    let aiTone = 'brotherly'; // Default to brotherly

    // If user is frustrated, be apologetic and brief but still supportive
    if (userFrustration > 0.7) {
      aiTone = 'brotherly'; // Stay brotherly but acknowledge frustration
      // Shorten response for frustrated users
      let condensed = baseResponse.split('. ').slice(0, 2).join('. ') + '.';
      return this.formatResponseWithEmotion(condensed, userEmotion, aiTone);
    }

    // If user is excited, be energetic and engaging
    if (userEmotion === 'VERY_POSITIVE') {
      aiTone = 'energetic';
      // Add enthusiasm
      let enhanced = baseResponse + ' This is exciting!';
      return this.formatResponseWithEmotion(enhanced, userEmotion, aiTone);
    }

    // If user seems lost or negative, be extra helpful and brotherly
    if (userEmotion === 'NEGATIVE' || userEmotion === 'SLIGHTLY_NEGATIVE') {
      aiTone = 'brotherly';
      // Add clarifying questions with friendly tone
      let helpful = baseResponse + ' Let me know if you need more help, buddy.';
      return this.formatResponseWithEmotion(helpful, userEmotion, aiTone);
    }

    // If same topic repeated, offer alternatives
    if (isRepeat) {
      aiTone = 'brotherly';
      let alternative = baseResponse + ' Want me to break it down differently?';
      return this.formatResponseWithEmotion(alternative, userEmotion, aiTone);
    }

    // Default: brotherly (warm, supportive, casual)
    return this.formatResponseWithEmotion(baseResponse, userEmotion, 'brotherly');
  }

  /**
   * Analyze conversation trajectory (is user becoming frustrated/happy?)
   */
  getConversationTrajectory() {
    if (this.conversationHistory.length < 3) return 'neutral';

    const recent = this.conversationHistory.slice(-5);
    const avgSentiment = recent.reduce((sum, msg) => sum + msg.sentiment, 0) / recent.length;

    if (avgSentiment > 0.5) return 'improving';
    if (avgSentiment < -0.5) return 'degrading';
    return 'stable';
  }

  /**
   * Reset emotion state (e.g., start new conversation)
   */
  reset() {
    this.userMood = 'NEUTRAL';
    this.conversationHistory = [];
    this.emotionalMemory = {};
    this.responseCount = 0;
  }
}

module.exports = EmotionEngine;
