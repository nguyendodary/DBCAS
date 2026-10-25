import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import BackgroundVideo from '../components/BackgroundVideo'
import { HeroBand } from '../components/SharedComponents'

function mockReducedMotion(matches) {
  const listeners = new Set()
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches,
    media: query,
    addEventListener: (name, fn) => listeners.add(fn),
    removeEventListener: (name, fn) => listeners.delete(fn),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    onchange: null,
    dispatchEvent: vi.fn(),
  }))
}

afterEach(() => {
  delete window.matchMedia
})

// The frontend prototype ships two looping mp4 backgrounds (landing + learner
// hero bands). These tests pin the mount contract so the video cannot regress
// to a static frame again: correct element, source, poster and loop flags.
describe('BackgroundVideo', () => {
  it('renders a looping muted inline video with poster for normal motion', () => {
    mockReducedMotion(false)
    const { container } = render(
      <BackgroundVideo className="hero-video" src="/media/hero.mp4" poster="/media/poster.jpg" />,
    )
    const video = container.querySelector('video.hero-video')
    expect(video).toBeInTheDocument()
    expect(video.autoplay).toBe(true)
    expect(video.muted).toBe(true)
    expect(video.loop).toBe(true)
    expect(video.playsInline).toBe(true)
    expect(video).toHaveAttribute('poster', '/media/poster.jpg')
    expect(video).toHaveAttribute('aria-hidden', 'true')
    expect(video.querySelector('source')).toHaveAttribute('src', '/media/hero.mp4')
    expect(video.querySelector('source')).toHaveAttribute('type', 'video/mp4')
  })

  it('keeps the poster frame without autoplay when reduced motion is set', () => {
    mockReducedMotion(true)
    const { container } = render(
      <BackgroundVideo src="/media/hero.mp4" poster="/media/poster.jpg" />,
    )
    const video = container.querySelector('video')
    expect(video.autoplay).toBe(false)
    expect(video).toHaveAttribute('preload', 'none')
    expect(video).toHaveAttribute('poster', '/media/poster.jpg')
    expect(video.muted).toBe(true)
    expect(video.loop).toBe(true)
  })

  it('resumes autoplay when the motion preference returns to normal', () => {
    mockReducedMotion(false)
    const { container } = render(<BackgroundVideo src="/media/hero.mp4" />)
    expect(container.querySelector('video').autoplay).toBe(true)
  })
})

describe('HeroBand video backdrop', () => {
  it('mounts the video and overlay when videoSrc is provided', () => {
    mockReducedMotion(false)
    const { container } = render(
      <HeroBand title="Hello" videoSrc="/media/hero.mp4" videoPoster="/media/poster.jpg" />,
    )
    expect(container.querySelector('video.hero-band-video')).toBeInTheDocument()
    expect(container.querySelector('.hero-band-video-overlay')).toBeInTheDocument()
  })

  it('renders no video elements without videoSrc', () => {
    mockReducedMotion(false)
    const { container } = render(<HeroBand title="Hello" />)
    expect(container.querySelector('video')).not.toBeInTheDocument()
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
