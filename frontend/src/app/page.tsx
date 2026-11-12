import { Navbar } from "@/components/marketing/Navbar";
import { HeroSection } from "@/components/marketing/HeroSection";
import { StatisticsStrip } from "@/components/marketing/StatisticsStrip";
import { AboutSection } from "@/components/marketing/AboutSection";
import { PlatformSection } from "@/components/marketing/PlatformSection";
import { WorkflowSection } from "@/components/marketing/WorkflowSection";
import { TechnologySection } from "@/components/marketing/TechnologySection";
import { SecuritySection } from "@/components/marketing/SecuritySection";
import { UseCasesSection } from "@/components/marketing/UseCasesSection";
import { FinalCTA } from "@/components/marketing/FinalCTA";
import { Footer } from "@/components/marketing/Footer";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#080909] text-[#F1EEE6] selection:bg-[#FF6A13] selection:text-[#080909]">
      <Navbar />
      <main>
        <HeroSection />
        <StatisticsStrip />
        <AboutSection />
        <PlatformSection />
        <WorkflowSection />
        <TechnologySection />
        <SecuritySection />
        <UseCasesSection />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
