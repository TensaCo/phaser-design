import { Hero } from '@/components/launch/Hero'
import { Economics } from '@/components/launch/Economics'
import { World } from '@/components/launch/World'
import { Close, Receipts } from '@/components/launch/Close'

export default function Page() {
  return (
    <main>
      <Hero />
      <Economics />
      <World />
      <Close />
      <Receipts />
    </main>
  )
}
