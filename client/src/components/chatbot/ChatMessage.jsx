import { useEffect, useRef } from 'react'

export default function ChatMessage({ message, isUser, timestamp, sources }) {
  const messageRef = useRef(null)

  useEffect(() => {
    // Auto-scroll to bottom when new message arrives
    if (messageRef.current) {
      messageRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [message])

  const formatTime = (ts) => {
    if (!ts) return ''
    const date = new Date(ts)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div
      ref={messageRef}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}
    >
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-2`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-purple-600'
              : 'bg-gradient-to-br from-purple-500 to-pink-600'
          }`}
        >
          {isUser ? (
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
              <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
            </svg>
          )}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div
            className={`rounded-2xl px-4 py-3 shadow-lg ${
              isUser
                ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-700'
            }`}
          >
            <p className="text-sm whitespace-pre-wrap break-words">{message}</p>
            
            {/* Sources */}
            {sources && sources.length > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Sources:</p>
                <div className="flex flex-wrap gap-1">
                  {sources.slice(0, 3).map((source, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-slate-600 dark:text-slate-300"
                    >
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* Timestamp */}
          {timestamp && (
            <span className="text-xs text-slate-500 dark:text-slate-400 mt-1 px-2">
              {formatTime(timestamp)}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
