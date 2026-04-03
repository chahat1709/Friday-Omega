// Simple NLP module for F.R.I.D.A.Y. backend
// Basic entity extraction, sentiment analysis, and intent detection

class NLP {
  static extractEntities(text) {
    // Basic entity extraction (placeholder)
    const entities = [];
    // Simple regex for common entities
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    const phoneRegex = /\b\d{10}\b/g;
    const urlRegex = /https?:\/\/[^\s]+/g;

    const emails = text.match(emailRegex) || [];
    const phones = text.match(phoneRegex) || [];
    const urls = text.match(urlRegex) || [];

    emails.forEach(email => entities.push({ type: 'email', value: email }));
    phones.forEach(phone => entities.push({ type: 'phone', value: phone }));
    urls.forEach(url => entities.push({ type: 'url', value: url }));

    return entities;
  }

  static sentiment(text) {
    // Basic sentiment analysis (placeholder)
    const positiveWords = ['good', 'great', 'awesome', 'happy', 'love', 'excellent'];
    const negativeWords = ['bad', 'terrible', 'hate', 'sad', 'angry', 'worst'];

    const lowerText = text.toLowerCase();
    let score = 0;

    positiveWords.forEach(word => {
      if (lowerText.includes(word)) score += 1;
    });

    negativeWords.forEach(word => {
      if (lowerText.includes(word)) score -= 1;
    });

    if (score > 0) return 'positive';
    if (score < 0) return 'negative';
    return 'neutral';
  }

  static parseIntent(text) {
    const intent = this.intent(text);
    const entities = this.extractEntities(text);
    const sentiment = this.sentiment(text);
    return {
      intent: intent,
      confidence: 0.8, // placeholder
      entities: entities,
      sentiment: sentiment
    };
  }

  static intent(text) {
    // Improved intent detection
    const lowerText = text.toLowerCase();

    // Time/Date queries
    if (lowerText.includes('what') && (lowerText.includes('time') || lowerText.includes('date'))) {
      if (lowerText.includes('date')) return 'date_query';
      return 'time_query';
    }

    // Weather
    if (lowerText.includes('weather')) return 'weather_query';

    // Reminders
    if (lowerText.includes('remind') || (lowerText.includes('reminder') && lowerText.includes('in'))) return 'create_reminder';

    // Search
    if (lowerText.includes('search') || (lowerText.includes('find') && lowerText.includes('for'))) return 'web_search';

    // App launch
    if (lowerText.includes('open') && lowerText.includes('app')) return 'open_app';

    // Device control
    if ((lowerText.includes('turn') || lowerText.includes('switch')) && (lowerText.includes('on') || lowerText.includes('off'))) return 'device_control';

    // Tasks
    if (lowerText.includes('exam') || lowerText.includes('task') || lowerText.includes('have') && lowerText.includes('tomorrow')) return 'add_task';

    // Volume control
    if (lowerText.includes('volume') || lowerText.includes('sound')) return 'volume_control';

    // Media control
    if (lowerText.includes('play') || lowerText.includes('music')) return 'media_control';

    return 'general_query';
  }
}

module.exports = NLP;