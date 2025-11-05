'use client';

import React from 'react';
import Nav from '@/components/landing/Nav';
import Hero from '@/components/landing/Hero';
import FeaturesGrid from '@/components/landing/FeaturesGrid';
import DemoSplit from '@/components/landing/DemoSplit';
import Testimonials from '@/components/landing/Testimonials';
import CTA from '@/components/landing/CTA';
import Footer from '@/components/landing/Footer';

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <Nav />
      <Hero />
      <FeaturesGrid />
      <DemoSplit />
      <Testimonials />
      <CTA />
      <Footer />
    </main>
  );
}
