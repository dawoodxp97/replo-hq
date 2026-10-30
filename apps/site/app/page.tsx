import Hero from '@/components/landing/Hero';
import DemoSplit from '@/components/landing/DemoSplit';
import FeaturesGrid from '@/components/landing/FeaturesGrid';
import Testimonials from '@/components/landing/Testimonials';
import CTA from '@/components/landing/CTA';

export default function LandingPage() {
  return (
    <>
      <Hero />
      <DemoSplit />
      <FeaturesGrid />
      <Testimonials />
      <CTA />
    </>
  );
}
