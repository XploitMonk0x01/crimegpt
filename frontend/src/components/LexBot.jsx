import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { legalService } from '../services/api';

const Message = ({ text, sender, sources = [], isError = false }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className={`flex flex-col gap-2 mb-12 ${sender === 'bot' ? 'items-start' : 'items-end'}`}
  >
    <div className="flex items-center gap-3 mb-2">
      <span className="label-mono text-[10px] text-muted-foreground">
        {sender === 'bot' ? 'LexBot System' : 'Officer Entry'}
      </span>
      <div className={`h-px w-8 bg-border ${sender === 'bot' ? 'order-first' : 'order-last'}`} />
    </div>

    <div className={`max-w-[85%] ${sender === 'bot' ? 'text-left' : 'text-right'}`}>
      <div className={`whitespace-pre-wrap text-base md:text-lg ${sender === 'bot'
          ? 'font-medium leading-relaxed text-foreground/90'
          : 'font-bold tracking-tight leading-snug text-accent/90'
        }`}>
        {text}
      </div>

      {sender === 'bot' && sources.length > 0 && (
        <div className="mt-6 flex flex-col gap-2 border-l-2 border-accent pl-4">
          <p className="label-mono text-[9px] text-muted-foreground mb-1">Legal References</p>
          {sources.map((source, idx) => (
            <div key={idx} className="flex items-center gap-2 group cursor-pointer">
              <span className="label-mono text-xs text-foreground group-hover:text-accent transition-colors">
                {source.act} • SECTION {source.section}
              </span>
              <span className="text-accent opacity-0 group-hover:opacity-100 transition-opacity">→</span>
            </div>
          ))}
        </div>
      )}
    </div>
  </motion.div>
);

export default function LexBot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: 'user', timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setHasStarted(true);

    try {
      const response = await legalService.query(input);
      const botMessage = {
        text: response.data.answer || response.data,
        sender: 'bot',
        timestamp: new Date(),
        sources: response.data.sources || []
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setMessages(prev => [...prev, {
        text: "Error connecting to Legal Intelligence Node. Please verify connection.",
        sender: 'bot',
        isError: true
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-full flex flex-col relative overflow-hidden bg-background">
      {/* Messages Area */}
      <AnimatePresence>
        {hasStarted && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex-1 overflow-y-auto p-8 scroll-smooth custom-scrollbar"
            ref={scrollRef}
          >
            <div className="max-w-4xl mx-auto space-y-8 pt-12 pb-32">
              {messages.map((msg, i) => (
                <Message key={i} {...msg} />
              ))}
              {isTyping && (
                <div className="label-mono text-accent animate-pulse text-[8px] mt-4">
                  [ Querying Legal Database... ]
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Centered Splash - Only visible when NO conversation */}
      <AnimatePresence>
        {!hasStarted && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-0"
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-64"
            >
              <p className="label-mono text-accent mb-2 tracking-[0.4em] uppercase text-[10px]">Autonomous Agent</p>
              <h1 className="text-5xl font-bold tracking-tighter uppercase leading-none">
                Legal Intelligence
              </h1>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Dynamic Input Container */}
      <div className={`flex flex-col transition-all duration-700 ease-[0.25, 0, 0, 1] ${hasStarted ? 'justify-end' : 'justify-center h-full'}`}>
        <motion.div
          layout
          className={`w-full z-10 ${hasStarted ? 'bg-background/80 backdrop-blur-xl border-t border-border/10 p-4' : 'p-8'}`}
        >
          <div className={`mx-auto transition-all duration-500 ${hasStarted ? 'max-w-5xl' : 'max-w-2xl'}`}>
            <div className="relative group">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask anything related to BNS 2023"
                className={`w-full bg-muted border-none tracking-tight placeholder:text-muted-foreground/20 focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all text-foreground/80 ${!hasStarted
                    ? 'text-center text-base px-8 py-3.5 shadow-2xl border border-border/20'
                    : 'text-sm px-6 py-2.5 shadow-none'
                  }`}
              />
              <button
                onClick={handleSend}
                className={`absolute top-1/2 -translate-y-1/2 bg-accent text-background hover:bg-foreground hover:text-background transition-all ${hasStarted ? 'right-2 p-2' : 'right-3 p-2.5'
                  }`}
              >
                <Send size={hasStarted ? 14 : 18} />
              </button>
            </div>


            <div className={`mt-3 flex items-center justify-between opacity-30 ${!hasStarted ? 'max-w-xs mx-auto justify-center gap-8' : ''}`}>
              <p className="label-mono text-[7px]">LEXBOT v0.1</p>
              <div className="flex gap-3">
                <span className="label-mono text-[7px] text-accent">SECURE</span>
                <span className="label-mono text-[7px]">NODE_AH01</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}






