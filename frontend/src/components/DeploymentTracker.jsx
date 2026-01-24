import React, { useState } from 'react';
import { Rocket, CheckCircle, XCircle, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import StarRating from './StarRating';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * DeploymentTracker component for collecting user feedback on deployed designs.
 *
 * Tracks:
 * - Whether the design was deployed
 * - Deployment success/failure
 * - Issues encountered
 * - User satisfaction rating
 * - Additional comments
 *
 * @param {string} designId - Unique identifier for the design
 * @param {string} requirements - The original requirements text (for context)
 */
export default function DeploymentTracker({ designId, requirements }) {
  const { token } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [deployed, setDeployed] = useState(false);
  const [success, setSuccess] = useState(true);
  const [environment, setEnvironment] = useState('dev');
  const [cloudProvider, setCloudProvider] = useState('azure');
  const [issues, setIssues] = useState('');
  const [modifications, setModifications] = useState('');
  const [rating, setRating] = useState(4);
  const [comments, setComments] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${BACKEND_URL}/feedback/deployment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          design_id: designId,
          deployed: deployed,
          deployment_date: deployed ? new Date().toISOString() : null,
          cloud_provider: cloudProvider,
          environment: environment,
          success: deployed ? success : true,
          issues_encountered: issues.trim() ? issues.split('\n').filter(i => i.trim()) : null,
          modifications_made: modifications.trim() || null,
          satisfaction_rating: rating,
          comments: comments.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit feedback');
      }

      setSubmitted(true);
    } catch (err) {
      console.error('Error submitting feedback:', err);
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Success state after submission
  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-full">
            <CheckCircle className="text-green-600" size={24} />
          </div>
          <div>
            <h3 className="font-semibold text-green-800">Thank You!</h3>
            <p className="text-sm text-green-600">
              Your feedback helps improve Carlos' architecture recommendations.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
      {/* Header - Always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-blue-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-full">
            <Rocket className="text-blue-600" size={20} />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-blue-800">Track This Design</h3>
            <p className="text-sm text-blue-600">
              Did you deploy this architecture? Share your experience!
            </p>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="text-blue-600" size={20} />
        ) : (
          <ChevronDown className="text-blue-600" size={20} />
        )}
      </button>

      {/* Expanded form */}
      {expanded && (
        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-5">
          {/* Deployed checkbox */}
          <div className="pt-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={deployed}
                onChange={(e) => setDeployed(e.target.checked)}
                className="w-5 h-5 rounded border-blue-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-slate-700">
                I deployed this design (or plan to)
              </span>
            </label>
          </div>

          {/* Deployment details - only shown if deployed */}
          {deployed && (
            <div className="space-y-4 pl-8 border-l-2 border-blue-200">
              {/* Environment selection */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Deployment Environment
                </label>
                <select
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="dev">Development</option>
                  <option value="staging">Staging</option>
                  <option value="prod">Production</option>
                  <option value="test">Test/Lab</option>
                </select>
              </div>

              {/* Cloud provider selection */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Cloud Provider
                </label>
                <select
                  value={cloudProvider}
                  onChange={(e) => setCloudProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="azure">Microsoft Azure</option>
                  <option value="aws">Amazon Web Services</option>
                  <option value="gcp">Google Cloud Platform</option>
                  <option value="multi_cloud">Multi-Cloud</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Success/Failure */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Deployment Status
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="success"
                      checked={success}
                      onChange={() => setSuccess(true)}
                      className="w-4 h-4 text-green-600 focus:ring-green-500"
                    />
                    <CheckCircle size={18} className="text-green-600" />
                    <span className="text-slate-700">Successful</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="success"
                      checked={!success}
                      onChange={() => setSuccess(false)}
                      className="w-4 h-4 text-red-600 focus:ring-red-500"
                    />
                    <XCircle size={18} className="text-red-600" />
                    <span className="text-slate-700">Had Issues</span>
                  </label>
                </div>
              </div>

              {/* Issues - only shown if deployment had issues */}
              {!success && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    What issues did you encounter?
                  </label>
                  <textarea
                    value={issues}
                    onChange={(e) => setIssues(e.target.value)}
                    placeholder="List any issues (one per line)&#10;e.g., Missing security groups&#10;AKS scaling didn't work as expected"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={4}
                  />
                </div>
              )}

              {/* Modifications made */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Did you modify the generated design?
                </label>
                <textarea
                  value={modifications}
                  onChange={(e) => setModifications(e.target.value)}
                  placeholder="Describe any changes you made to the architecture or Terraform code (optional)"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                />
              </div>
            </div>
          )}

          {/* Satisfaction rating - always shown */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Overall Satisfaction with This Design
            </label>
            <div className="flex items-center gap-4">
              <StarRating value={rating} onChange={setRating} size="md" />
              <span className="text-sm text-slate-500">
                {rating === 1 && 'Poor'}
                {rating === 2 && 'Fair'}
                {rating === 3 && 'Good'}
                {rating === 4 && 'Very Good'}
                {rating === 5 && 'Excellent'}
              </span>
            </div>
          </div>

          {/* Additional comments */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              <MessageSquare size={16} className="inline mr-1" />
              Additional Comments (optional)
            </label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Any other feedback to help improve Carlos..."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Submit button */}
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-colors ${
                submitting
                  ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {submitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
            <button
              type="button"
              onClick={() => setExpanded(false)}
              className="px-6 py-3 rounded-lg font-medium bg-slate-200 text-slate-700 hover:bg-slate-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
