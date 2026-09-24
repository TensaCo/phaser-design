import { Hero } from '@/components/launch/Hero'
import { Light } from '@/components/launch/Light'
import { MachineSection } from '@/components/launch/Machine'
import { World } from '@/components/launch/World'
import { Footer } from '@/components/launch/Close'

export default function Page() {
  return (
    <main>
      <Hero />
      <Light />
      <MachineSection />
      <World />
      <Footer />
    </main>
  )
}
