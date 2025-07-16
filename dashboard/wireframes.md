# GoodBooks Recommender Dashboard Wireframes

## Design Principles
- **Clean, modern interface** with intuitive navigation
- **Mobile-first responsive design** for all screen sizes
- **High contrast** for accessibility and readability
- **Fast loading** with optimized assets and lazy loading
- **Real-time updates** with minimal page refreshes

## Color Palette
- **Primary**: #2563eb (Blue)
- **Secondary**: #059669 (Green)
- **Accent**: #dc2626 (Red)
- **Background**: #f8fafc (Light Gray)
- **Text**: #1e293b (Dark Gray)
- **Borders**: #e2e8f0 (Light Border)

## Typography
- **Headers**: Inter, sans-serif (Bold)
- **Body**: Inter, sans-serif (Regular)
- **Monospace**: Fira Code, monospace

---

## Page 1: Main Dashboard Landing

```
┌─────────────────────────────────────────────────────────────────┐
│ [📚 GoodBooks] [Home] [Search] [Analytics] [Settings] [Profile] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 System Health                         🔥 Quick Actions      │
│  ┌─────────────────────┐                 ┌─────────────────────┐│
│  │ Status: ✅ Healthy  │                 │ [Get Recommendations]││
│  │ Uptime: 24h 15m     │                 │ [Search Books]      ││
│  │ Requests: 1.2k/min  │                 │ [View Analytics]    ││
│  │ Cache Hit: 89%      │                 │ [Export Data]       ││
│  └─────────────────────┘                 └─────────────────────┘│
│                                                                 │
│  📈 Recent Activity                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Live Recommendations Chart                                 ││
│  │ [Interactive Chart showing recommendations over time]      ││
│  │                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  📚 Featured Books                      🎯 Top Recommendations  │
│  ┌─────────────────────┐                ┌─────────────────────┐│
│  │ [Book Cover]        │                │ 1. The Great Gatsby ││
│  │ "The Hunger Games"  │                │    ⭐ 4.2 (95% rec) ││
│  │ by Suzanne Collins  │                │ 2. 1984             ││
│  │ ⭐ 4.34 (4.8M)      │                │    ⭐ 4.19 (89% rec)││
│  └─────────────────────┘                │ 3. Harry Potter     ││
│                                         │    ⭐ 4.44 (92% rec)││
│                                         └─────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Page 2: Book Recommendations Interface

```
┌─────────────────────────────────────────────────────────────────┐
│ [📚 GoodBooks] > Recommendations                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🎯 Get Personalized Recommendations                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Recommendation Type:                                       ││
│  │ ○ User-based (ID: [____]) ○ Book-based ([Search Book])    ││
│  │                                                           ││
│  │ Number of recommendations: [5 ▼]                          ││
│  │ ☑ Include explanations   ☐ Cache results                 ││
│  │                                                           ││
│  │ [Get Recommendations] [Reset]                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  📋 Results (5 recommendations, 245ms)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 1. ┌────────────────────────────────────────────────────┐   ││
│  │    │ [Cover] "To Kill a Mockingbird"                   │   ││
│  │    │         by Harper Lee                              │   ││
│  │    │         ⭐ 4.27 (3.2M ratings) | Score: 0.89      │   ││
│  │    │         📖 Fiction, Classics                       │   ││
│  │    │         💡 "Similar themes to your liked books"   │   ││
│  │    │         [View Details] [Explain] [Add to List]    │   ││
│  │    └────────────────────────────────────────────────────┘   ││
│  │                                                           ││
│  │ 2. [Similar card format for next recommendation]         ││
│  │ 3. [Similar card format for next recommendation]         ││
│  │ 4. [Similar card format for next recommendation]         ││
│  │ 5. [Similar card format for next recommendation]         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Page 3: Book Search Interface

```
┌─────────────────────────────────────────────────────────────────┐
│ [📚 GoodBooks] > Search                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔍 Advanced Book Search                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Search: [fantasy adventure magic              ] [🔍 Search] ││
│  │                                                           ││
│  │ Filters: ▼ Genre [All] ▼ Rating [All] ▼ Year [All]       ││
│  │         Results: [10 ▼] Threshold: [0.3    ]            ││
│  │         ☑ Include explanations ☐ Semantic search        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  📚 Search Results (127 books found, 89ms)                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ┌──────────┬─────────────────────────────────────────────┐ ││
│  │ │ [Cover]  │ "Harry Potter and the Philosopher's Stone" │ ││
│  │ │ Image    │ by J.K. Rowling                            │ ││
│  │ │          │ ⭐ 4.44 (4.6M) | Match: 95%               │ ││
│  │ │          │ 📖 Fantasy, Young Adult | 📅 1997         │ ││
│  │ │          │ 💡 Strong match for fantasy adventure      │ ││
│  │ │          │ [Details] [Recommend] [Add to List]       │ ││
│  │ └──────────┴─────────────────────────────────────────────┘ ││
│  │                                                           ││
│  │ [Similar format for 9 more search results...]            ││
│  │                                                           ││
│  │ [← Previous] Page 1 of 13 [Next →]                       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Page 4: Book Details & Explanation

```
┌─────────────────────────────────────────────────────────────────┐
│ [📚 GoodBooks] > Book Details                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📖 "To Kill a Mockingbird"                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ┌────────────┬───────────────────────────────────────────┐ ││
│  │ │ [Large     │ by Harper Lee                             │ ││
│  │ │  Book      │ ⭐ 4.27 (3,198,671 ratings)              │ ││
│  │ │  Cover     │ 📖 Fiction, Classics, Historical Fiction  │ ││
│  │ │  Image]    │ 📅 Published: 1960 | 📄 376 pages        │ ││
│  │ │            │ 🏢 Publisher: J.B. Lippincott & Co.      │ ││
│  │ │            │ 🌐 Language: English                      │ ││
│  │ │            │                                          │ ││
│  │ │            │ [📚 Get Recommendations] [💾 Save]       │ ││
│  │ └────────────┴───────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  🤖 AI Explanation                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Why this book is recommended:                              ││
│  │                                                           ││
│  │ "Based on your interest in classic American literature    ││
│  │ and social justice themes, 'To Kill a Mockingbird'       ││
│  │ is highly recommended. The book explores themes of       ││
│  │ racial injustice and moral growth that align with your   ││
│  │ reading preferences."                                     ││
│  │                                                           ││
│  │ Similar books you might enjoy:                            ││
│  │ • "The Great Gatsby" (87% similarity)                    ││
│  │ • "Of Mice and Men" (82% similarity)                     ││
│  │ • "The Catcher in the Rye" (79% similarity)             ││
│  │                                                           ││
│  │ Confidence Score: 89% | Processing time: 156ms           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Page 5: Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│ [📚 GoodBooks] > Analytics                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 System Performance                   📈 Recommendation Stats │
│  ┌─────────────────────┐                ┌─────────────────────┐│
│  │ Requests/min: 1,247 │                │ Total: 125,430      ││
│  │ Avg Response: 89ms  │                │ Today: 2,341        ││
│  │ Cache Hit: 92%      │                │ Success Rate: 99.7% ││
│  │ Error Rate: 0.3%    │                │ Avg Score: 0.78     ││
│  └─────────────────────┘                └─────────────────────┘│
│                                                                 │
│  📉 Performance Chart (Last 24 Hours)                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [Interactive line chart showing:]                          ││
│  │ - Request volume over time                                 ││
│  │ - Response time trends                                     ││
│  │ - Cache hit ratios                                         ││
│  │ - Error rates                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  🏆 Top Books                           🔥 Popular Genres      │
│  ┌─────────────────────┐                ┌─────────────────────┐│
│  │ 1. Harry Potter     │                │ 1. Fiction (45%)    ││
│  │    4,231 recs       │                │ 2. Fantasy (23%)    ││
│  │ 2. The Hunger Games │                │ 3. Romance (18%)    ││
│  │    3,892 recs       │                │ 4. Mystery (14%)    ││
│  │ 3. 1984             │                │ 5. Sci-Fi (12%)     ││
│  │    3,445 recs       │                │ 6. Young Adult (8%) ││
│  └─────────────────────┘                └─────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Mobile Responsive Design

### Mobile Layout (< 768px)
```
┌─────────────────────┐
│ [☰] GoodBooks      │
├─────────────────────┤
│                     │
│ 📊 Health           │
│ ┌─────────────────┐ │
│ │ ✅ Online       │ │
│ │ 1.2k req/min    │ │
│ └─────────────────┘ │
│                     │
│ 🎯 Quick Actions    │
│ ┌─────────────────┐ │
│ │ [Recommend]     │ │
│ │ [Search]        │ │
│ │ [Analytics]     │ │
│ └─────────────────┘ │
│                     │
│ 📚 Featured         │
│ ┌─────────────────┐ │
│ │ [Book Card]     │ │
│ │ Title           │ │
│ │ ⭐ Rating       │ │
│ └─────────────────┘ │
│                     │
│ [Bottom Navigation] │
└─────────────────────┘
```

## Interaction Flows

### Flow 1: Get Recommendations
1. User selects recommendation type (user-based or content-based)
2. User enters user ID or book title
3. User sets number of recommendations and options
4. System calls `/recommendations` API endpoint
5. Display results with explanations if requested
6. User can click "Explain" for detailed explanation via `/explain` endpoint

### Flow 2: Search Books
1. User enters search query with optional filters
2. System calls `/search` API endpoint with semantic search
3. Display search results with similarity scores
4. User can view book details and get recommendations
5. User can refine search with additional filters

### Flow 3: View Explanations
1. User clicks "Explain" on any recommendation
2. System calls `/explain` endpoint with book ID
3. Display AI-generated explanation with context
4. Show similar books and confidence scores
5. User can explore related recommendations

### Flow 4: Session Management
1. System automatically creates session via `/session` endpoint
2. Track user interactions and preferences
3. Store session data in Redis backend
4. Use session for personalized recommendations
5. Allow manual session management in settings

## Accessibility Features
- **Keyboard navigation** for all interactive elements
- **Screen reader support** with proper ARIA labels
- **High contrast mode** option
- **Text size adjustment** controls
- **Focus indicators** for keyboard users
- **Alt text** for all images and charts

## Performance Optimizations
- **Lazy loading** for book cover images
- **Virtual scrolling** for large result sets
- **Debounced search** to reduce API calls
- **Caching** of frequent requests
- **Compressed assets** and minified code
- **Progressive enhancement** for slower connections
