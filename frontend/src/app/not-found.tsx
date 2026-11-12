import Link from "next/link";
import { ArrowLeft, Radar } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#07090C] text-[#F5F7FA] flex items-center justify-center p-6">
      <div className="max-w-md w-full rounded border border-white/[0.08] bg-[#0E1217] p-8 text-center">
        <div className="w-12 h-12 rounded bg-[#00E5FF]/10 border border-[#00E5FF]/30 flex items-center justify-center mx-auto mb-5">
          <Radar className="w-6 h-6 text-[#00E5FF]" />
        </div>
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-[#00E5FF]">
          [ ERROR 404 ]
        </p>
        <h1 className="text-2xl font-bold mt-2">Trace Path Not Found</h1>
        <p className="text-xs text-[#8A929E] mt-2 leading-relaxed">
          The requested forensic route or investigation node does not exist in this
          workspace.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#00E5FF] text-[#000000] text-xs font-mono font-semibold uppercase"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Command Center
          </Link>
          <Link
            href="/"
            className="px-4 py-2 rounded border border-white/[0.12] text-xs font-mono uppercase text-[#F5F7FA] hover:border-[#00E5FF]/50"
          >
            Landing
          </Link>
        </div>
      </div>
    </div>
  );
}
