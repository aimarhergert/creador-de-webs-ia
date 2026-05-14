"use client";

import { X, ExternalLink, RefreshCw } from "lucide-react";
import { useState } from "react";

interface Props {
  url: string;
  keyword: string;
  onClose: () => void;
}

export default function AssetPreview({ url, keyword, onClose }: Props) {
  const [loading, setLoading] = useState(true);
  const [key, setKey] = useState(0);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/80 backdrop-blur-sm">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-gray-950 border-b border-gray-800 shrink-0">
        <span className="text-sm text-gray-300 font-medium truncate flex-1">{keyword}</span>
        <code className="text-xs text-blue-400 hidden sm:block max-w-sm truncate">{url}</code>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => { setLoading(true); setKey(k => k + 1); }}
            className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded transition-colors"
            title="Recargar"
          >
            <RefreshCw size={13} />
          </button>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded transition-colors"
            title="Abrir en nueva pestaña"
          >
            <ExternalLink size={13} />
          </a>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded transition-colors ml-1"
            title="Cerrar"
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Frame */}
      <div className="flex-1 relative bg-gray-900">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-600 text-sm gap-2">
            <RefreshCw size={14} className="animate-spin" />
            Cargando preview…
          </div>
        )}
        <iframe
          key={key}
          src={url}
          onLoad={() => setLoading(false)}
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          className="w-full h-full border-0"
          title={keyword}
        />
      </div>
    </div>
  );
}
