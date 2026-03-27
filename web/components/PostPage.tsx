import Markdown from '@/components/Markdown';
import TOCMobile from '@/components/TOCMobile';
import TOCDesktop from '@/components/TOCDesktop';
import { extractTocFromMarkdown } from '@/lib/toc';
import fs from 'fs';
import path from 'path';

interface PostPageProps {
  showToc?: boolean;
}

export default async function PostPage({ showToc = true }: PostPageProps) {
  // Read content from README.md (one level up from web directory)
  const readmePath = path.join(process.cwd(), '..', 'README.md');
  let content: string;
  
  try {
    content = fs.readFileSync(readmePath, 'utf8');
  } catch (error) {
    console.error('Error reading README.md:', error);
    content = `# Alpha Vantage MCP

Error loading README.md content.`;
  }
  
  const tocItems = showToc ? extractTocFromMarkdown(content) : [];

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'rgb(45, 45, 45)' }}>
        {/* Header */}
        <header className="w-full pt-8 pb-4 px-4 sm:px-8">
          <div className="flex justify-center">
            <div className="w-full sm:w-[50%] 2xl:w-[40%] max-w-[100%] flex justify-between items-center">
            <a href="https://www.alphavantage.co/" className="text-white text-xl tracking-wider transition-colors">
              ALPHA <span className="font-light">VANTAGE</span>
            </a>
            <div className="flex space-x-6">
              <a href="https://www.alphavantage.co/" className="hover:text-green-300 transition-colors" style={{ color: '#42DCA3' }}>
                Alpha Vantage Home
              </a>
              <a href="https://www.alphavantage.co/documentation/" className="hover:text-green-300 transition-colors" style={{ color: '#42DCA3' }}>
                API Documentation
              </a>
            </div>
            </div>
          </div>
        </header>
        {/* Mobile TOC */}
        {showToc && <TOCMobile tocItems={tocItems} />}
        
        <main className="flex-1">
          {/* Main content with messages and TOC */}
          <div className="flex justify-center">
            {/* Table of Contents (Desktop) */}
            <div className="hidden sm:block sm:w-[20%] h-[calc(50vh)] fixed left-8 top-24 2xl:left-40">
              {showToc && <TOCDesktop tocItems={tocItems} />}
            </div>

            {/* Messages (centered) */}
            <div className={`flex flex-col px-4 sm:px-0 pt-4 w-full sm:w-[50%] 2xl:w-[40%] max-w-[100%] space-y-4`}>
              {/* Article */}
              <article className="rounded-lg shadow-sm p-4 sm:p-6 lg:p-8" style={{ backgroundColor: '#1f1f1f', border: '1px solid rgba(74, 222, 128, 0.3)' }}>
                {/* Logo Section */}
                <div className="mb-12 text-center">
                  <img src="https://www.alphavantage.co/logo.png" alt="Alpha Vantage Logo" className="mx-auto h-16 mb-8" />
                </div>
                <div className="prose prose-lg prose-slate dark:prose-invert max-w-none">
                  <Markdown content={content} />
                </div>
              </article>
            </div>
          </div>
        </main>
        
        <footer className="w-full py-8">
          <div className="text-center text-gray-400 text-sm">
            <p>
              Made with love at
              <a href="https://www.alphavantage.co/" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: '#42DCA3' }}> Alpha Vantage</a>. Happy hacking!
            </p>
            <p className="mt-2">
              <a href="https://www.alphavantage.co/privacy/" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: '#42DCA3' }}>Privacy Policy</a>
            </p>
          </div>
        </footer>
      </div>
  );
}
