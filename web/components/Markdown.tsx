'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Components } from 'react-markdown';
import { generateSlug } from '@/lib/toc';

interface MarkdownProps {
  content: string;
  className?: string;
}

// Custom components for ReactMarkdown
const markdownComponents: Components = {
  h1: () => {
    return <div></div>
  },
  h2: ({ children }) => {
    const text = children?.toString() || '';
    const id = generateSlug(text);
    return (
      <h2 
        id={id}
className="text-3xl font-light mb-8" style={{ color: '#42DCA3' }}
      >
        {children}
      </h2>
    );
  },
  h3: ({ children }) => {
    const text = children?.toString() || '';
    const id = generateSlug(text);
    return (
      <h3 
        id={id}
        className="text-2xl font-light mb-6" style={{ color: '#42DCA3' }}
      >
        {children}
      </h3>
    );
  },
  h4: ({ children }) => (
    <h4 className="text-xl font-semibold mb-4" style={{ color: '#42DCA3' }}>
      {children}
    </h4>
  ),
  h5: ({ children }) => (
    <h5 className="text-base sm:text-lg font-bold mt-3 mb-1" style={{ color: 'white' }}>
      {children}
    </h5>
  ),
  h6: ({ children }) => (
    <h6 className="text-sm sm:text-base font-bold mt-3 mb-1" style={{ color: 'white' }}>
      {children}
    </h6>
  ),
  p: ({ children }) => (
    <p className="mb-4" style={{ color: '#d1d5db' }}>
      {children}
    </p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-6 space-y-2 mb-4">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-6 space-y-2 mb-4">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li style={{ color: '#d1d5db' }}>
      {children}
    </li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 pl-4 py-2 mb-4 rounded-r-md" style={{ borderLeftColor: 'rgba(74, 222, 128, 0.3)', backgroundColor: '#1f1f1f' }}>
      <div className="italic" style={{ color: '#9ca3af' }}>
        {children}
      </div>
    </blockquote>
  ),
  a: ({ href, children, onClick, ...props }) => {
    const isExternal = href && (href.startsWith('http') || href.startsWith('https'));

    // Handle onclick string conversion
    const handleClick = onClick && typeof onClick === 'string'
      ? () => {
          try {
            // Execute the onclick string as code (for gtag calls etc.)
            eval(onClick);
          } catch (error) {
            console.error('Error executing onclick:', error);
          }
        }
      : onClick;

    return (
      <a
        href={href}
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noopener noreferrer' : undefined}
        className="hover:underline" style={{ color: '#42DCA3' }}
        onClick={handleClick}
        {...props}
      >
        {children}
      </a>
    );
  },
  strong: ({ children }) => (
    <strong style={{ color: '#42DCA3' }}>
      {children}
    </strong>
  ),
  em: ({ children }) => (
    <em className="italic" style={{ color: '#9ca3af' }}>
      {children}
    </em>
  ),
  code: ({ children, className, ...props }) => {
    const content = children?.toString().trim() || '';
    
    // If it's an empty code block, don't render anything
    if (content.length === 0) {
      return null;
    }

    return (
      <code 
        className={`px-2 py-1 rounded text-sm ${className || ''}`}
        style={{ 
          backgroundColor: '#1f1f1f', 
          color: '#42DCA3', 
          border: '1px solid rgba(74, 222, 128, 0.3)' 
        }} 
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children, ...props }) => {
    const [copied, setCopied] = React.useState(false);
    
    const handleCopy = () => {
      // Extract text content from children
      const extractText = (node: any): string => {
        if (typeof node === 'string') return node;
        if (Array.isArray(node)) return node.map(extractText).join('');
        if (node?.props?.children) return extractText(node.props.children);
        return node?.toString() || '';
      };
      
      const textContent = extractText(children);
      navigator.clipboard.writeText(textContent).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    };

    return (
      <div className="relative group">
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-105 cursor-pointer"
          style={{ 
            backgroundColor: 'rgba(66, 220, 163, 0.1)', 
            color: '#42DCA3',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(66, 220, 163, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(66, 220, 163, 0.1)';
          }}
          title="Copy to clipboard"
        >
          {copied ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
            </svg>
          )}
        </button>
        <pre 
          className="p-4 rounded text-sm overflow-x-auto my-4" 
          style={{ backgroundColor: '#1f1f1f', color: '#42DCA3', border: '1px solid rgba(74, 222, 163, 0.3)' }} 
          {...props}
        >
          {children}
        </pre>
      </div>
    );
  },
  hr: () => (
    <hr className="my-8 border-t" style={{ borderColor: 'rgba(74, 222, 128, 0.3)' }} />
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-6">
      <table className="w-full border-collapse">
        {children}
      </table>
    </div>
  ),
  th: ({ children }) => (
    <th className="px-4 py-2" style={{ border: '1px solid rgba(74, 222, 128, 0.3)', color: '#42DCA3', backgroundColor: '#1f1f1f' }}>
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2" style={{ border: '1px solid rgba(74, 222, 128, 0.3)', color: '#d1d5db' }}>
      {children}
    </td>
  ),
  div: ({ className, ...props }) => {
    // Regular div
    return <div className={className} {...props} />;
  },
  details: ({ children }) => (
    <details className="mb-4 rounded-lg border overflow-hidden details-container" style={{ borderColor: 'rgba(74, 222, 128, 0.3)', backgroundColor: '#1f1f1f' }}>
      {children}
    </details>
  ),
  summary: ({ children }) => (
    <summary className="cursor-pointer font-semibold rounded-t-lg hover:opacity-80" style={{ backgroundColor: 'rgba(66, 220, 163, 0.1)', color: '#42DCA3', padding: '1rem' }}>
      {children}
    </summary>
  ),
};

// Function to parse Hugo shortcodes and convert YouTube links
function parseShortcodes(content: string): string {
  let processedContent = content;
  
  // Replace {{< rawhtml >}} shortcodes with the HTML content inside
  const rawhtmlRegex = /\{\{<\s*rawhtml\s*>\}\}([\s\S]*?)\{\{<\s*\/rawhtml\s*>\}\}/g;
  processedContent = processedContent.replace(rawhtmlRegex, (_, htmlContent) => {
    // Return the HTML content with proper spacing
    return htmlContent.trim();
  });
  
  // Convert YouTube image links to iframe embeds
  // Support both img.youtube.com and i3.ytimg.com (and other ytimg subdomains)
  const youtubePattern = /\[!\[([^\]]*)\]\(https?:\/\/(?:img\.youtube\.com|i\d*\.ytimg\.com)\/vi\/([^\/]+)\/[^)]+\)\]\(https:\/\/www\.youtube\.com\/watch\?v=([^)]+)\)/g;
  processedContent = processedContent.replace(youtubePattern, '<div class="youtube-embed mb-6 text-center"><iframe width="560" height="315" src="https://www.youtube.com/embed/$3" frameborder="0" allowfullscreen class="w-full max-w-2xl mx-auto rounded-lg"></iframe></div>');
  
  return processedContent;
}

export default function Markdown({ content, className = '' }: MarkdownProps) {
  // Preprocess content to handle Hugo shortcodes
  const processedContent = parseShortcodes(content);

  // Add error boundary and validation for content
  if (!processedContent || typeof processedContent !== 'string') {
    console.error('Invalid markdown content:', processedContent);
    return <div className="text-red-500">Error: Invalid content</div>;
  }

  return (
    <div className={`prose max-w-none ${className}`}>
      <style jsx global>{`
        pre code {
          border: none !important;
          padding: 0 !important;
        }
        
        pre::-webkit-scrollbar {
          height: 8px;
        }
        
        pre::-webkit-scrollbar-track {
          background: #1f1f1f;
        }
        
        pre::-webkit-scrollbar-thumb {
          background: rgba(66, 220, 163, 0.3);
          border-radius: 4px;
        }
        
        pre::-webkit-scrollbar-thumb:hover {
          background: rgba(66, 220, 163, 0.5);
        }

        .details-container[open] {
          padding: 0 1rem 1rem 1rem;
        }

        .details-container[open] summary {
          border-bottom: 1px solid rgba(74, 222, 128, 0.3);
          margin: 0 -1rem 1rem -1rem;
          padding: 1rem;
        }
      `}</style>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={markdownComponents}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}
