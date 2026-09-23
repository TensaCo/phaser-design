import { Hero } from '@/components/hero/Hero'
import { ComputeCurve } from '@/components/curve/ComputeCurve'
import { Unlocks } from '@/components/unlocks/Unlocks'
import { Footer } from '@/components/Footer'

export default function Page() {
  return (
    <main>
      <a className="skip" href="#curve-title">Skip to the compute curve</a>
      <Hero />
      <ComputeCurve />
      <Unlocks />
      <Footer />
    </main>
  )
}
