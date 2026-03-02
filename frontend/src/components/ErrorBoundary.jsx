// frontend/src/components/ErrorBoundary.jsx
import { Component } from 'react';
import './ErrorBoundary.css';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="eb-wrapper">
          <div className="eb-card">
            <div className="eb-icon">⚠</div>
            <h2 className="eb-title">Something went wrong</h2>
            <p className="eb-message">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <div className="eb-actions">
              <button className="eb-btn eb-btn--primary" onClick={this.handleReset}>
                Try again
              </button>
              <button className="eb-btn eb-btn--secondary" onClick={() => window.location.reload()}>
                Reload page
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}