import { Component } from 'react'
import { message } from '../i18n'
import { ErrorState } from './States'

export default class ErrorBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }

  render() {
    if (this.state.failed) return <main className="mx-auto max-w-xl p-8">
      <ErrorState message={message('errors.unknown')} onRetry={this.props.onRetry || (() => window.location.reload())} />
    </main>
    return this.props.children
  }
}
