import React, { useState, useEffect } from 'react';
import { BarChart3, Star, CheckCircle, XCircle, TrendingUp, AlertTriangle, Filter, RefreshCw, MessageSquare } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * FeedbackDashboard component displays deployment feedback analytics and history.
 * Shows aggregated stats, success rates, and individual feedback entries.
 */
export default function FeedbackDashboard() {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [cloudFilter, setCloudFilter] = useState('all');
  const [envFilter, setEnvFilter] = useState('all');
  const [ratingFilter, setRatingFilter] = useState('all');

  const fetchData = async () => {
    try {
      setError(null);

      // Fetch analytics and feedback list in parallel
      const [analyticsRes, feedbackRes] = await Promise.all([
        fetch(`${BACKEND_URL}/feedback/analytics`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/feedback/my-feedback`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (!analyticsRes.ok || !feedbackRes.ok) {
        throw new Error('Failed to fetch feedback data');
      }

      const analyticsData = await analyticsRes.json();
      const feedbackData = await feedbackRes.json();

      setAnalytics(analyticsData);
      setFeedback(feedbackData.feedback || []);
    } catch (err) {
      console.error('Error fetching feedback:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Filter feedback
  const filteredFeedback = feedback.filter(fb => {
    if (cloudFilter !== 'all' && fb.cloud_provider !== cloudFilter) return false;
    if (envFilter !== 'all' && fb.environment !== envFilter) return false;
    if (ratingFilter !== 'all') {
      const rating = fb.satisfaction_rating;
      if (ratingFilter === 'high' && rating < 4) return false;
      if (ratingFilter === 'medium' && (rating < 3 || rating > 3)) return false;
      if (ratingFilter === 'low' && rating > 2) return false;
    }
    return true;
  });

  // Get unique values for filters
  const cloudProviders = [...new Set(feedback.map(fb => fb.cloud_provider).filter(Boolean))];
  const environments = [...new Set(feedback.map(fb => fb.environment).filter(Boolean))];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-blue-500" size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <AlertTriangle className="text-red-500" size={24} />
          <div>
            <h3 className="font-semibold text-red-800">Error Loading Feedback</h3>
            <p className="text-sm text-red-600">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-sm text-red-700 underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <BarChart3 size={24} className="text-blue-600" />
          Deployment Feedback Dashboard
        </h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 transition disabled:opacity-50"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<MessageSquare size={20} />}
            label="Total Feedback"
            value={analytics.total_feedback}
            color="blue"
          />
          <StatCard
            icon={<TrendingUp size={20} />}
            label="Deployment Rate"
            value={`${analytics.deployment_rate?.toFixed(1) || 0}%`}
            color="purple"
          />
          <StatCard
            icon={<CheckCircle size={20} />}
            label="Success Rate"
            value={`${analytics.success_rate?.toFixed(1) || 0}%`}
            color="green"
          />
          <StatCard
            icon={<Star size={20} />}
            label="Avg Rating"
            value={analytics.average_rating?.toFixed(1) || 'N/A'}
            suffix="/5"
            color="amber"
          />
        </div>
      )}

      {/* Rating Distribution */}
      {analytics?.rating_distribution && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Rating Distribution</h3>
          <div className="space-y-3">
            {[5, 4, 3, 2, 1].map(rating => {
              const count = analytics.rating_distribution[rating] || 0;
              const total = analytics.total_feedback || 1;
              const percentage = (count / total) * 100;
              return (
                <div key={rating} className="flex items-center gap-3">
                  <div className="flex items-center gap-1 w-16">
                    <Star size={14} className="text-amber-500 fill-amber-500" />
                    <span className="text-sm font-medium text-slate-700">{rating}</span>
                  </div>
                  <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-400 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-slate-500 w-12 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Common Issues */}
      {analytics?.common_issues && analytics.common_issues.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-amber-800 mb-4 flex items-center gap-2">
            <AlertTriangle size={20} />
            Common Issues Reported
          </h3>
          <ul className="space-y-2">
            {analytics.common_issues.map((issue, idx) => (
              <li key={idx} className="flex items-start gap-2 text-amber-700">
                <span className="text-amber-500 mt-1">-</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Filters */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Filter size={16} className="text-slate-500" />
          <span className="text-sm font-medium text-slate-600">Filters</span>
        </div>
        <div className="flex flex-wrap gap-4">
          <select
            value={cloudFilter}
            onChange={(e) => setCloudFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
          >
            <option value="all">All Providers</option>
            {cloudProviders.map(provider => (
              <option key={provider} value={provider}>
                {provider === 'azure' ? 'Azure' :
                 provider === 'aws' ? 'AWS' :
                 provider === 'gcp' ? 'GCP' :
                 provider === 'multi_cloud' ? 'Multi-Cloud' : provider}
              </option>
            ))}
          </select>

          <select
            value={envFilter}
            onChange={(e) => setEnvFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
          >
            <option value="all">All Environments</option>
            {environments.map(env => (
              <option key={env} value={env}>
                {env === 'dev' ? 'Development' :
                 env === 'staging' ? 'Staging' :
                 env === 'prod' ? 'Production' :
                 env === 'test' ? 'Test/Lab' : env}
              </option>
            ))}
          </select>

          <select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
          >
            <option value="all">All Ratings</option>
            <option value="high">High (4-5 stars)</option>
            <option value="medium">Medium (3 stars)</option>
            <option value="low">Low (1-2 stars)</option>
          </select>
        </div>
      </div>

      {/* Feedback List */}
      <div>
        <h3 className="text-lg font-semibold text-slate-800 mb-4">
          Feedback History ({filteredFeedback.length})
        </h3>

        {filteredFeedback.length === 0 ? (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center">
            <MessageSquare size={48} className="mx-auto text-slate-300 mb-3" />
            <p className="text-slate-500">
              {feedback.length === 0
                ? 'No feedback submitted yet. Deploy a design and share your experience!'
                : 'No feedback matches the current filters.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredFeedback.map((fb) => (
              <FeedbackCard key={fb.id} feedback={fb} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, suffix = '', color }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
  };

  return (
    <div className={`border rounded-xl p-4 ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs font-semibold uppercase tracking-wide opacity-75">{label}</span>
      </div>
      <div className="text-2xl font-bold">
        {value}
        {suffix && <span className="text-sm font-normal opacity-60">{suffix}</span>}
      </div>
    </div>
  );
}

function FeedbackCard({ feedback }) {
  const [expanded, setExpanded] = useState(false);

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const getProviderLabel = (provider) => {
    const labels = {
      azure: 'Azure',
      aws: 'AWS',
      gcp: 'GCP',
      multi_cloud: 'Multi-Cloud',
    };
    return labels[provider] || provider;
  };

  const getEnvLabel = (env) => {
    const labels = {
      dev: 'Development',
      staging: 'Staging',
      prod: 'Production',
      test: 'Test/Lab',
    };
    return labels[env] || env;
  };

  return (
    <div
      className="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Requirements Summary */}
          <p className="font-medium text-slate-800 mb-2">
            {feedback.requirements_summary || 'No requirements summary'}
          </p>

          {/* Meta info */}
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="text-slate-500">{formatDate(feedback.created_at)}</span>

            {feedback.cloud_provider && (
              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                {getProviderLabel(feedback.cloud_provider)}
              </span>
            )}

            {feedback.environment && (
              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-medium">
                {getEnvLabel(feedback.environment)}
              </span>
            )}

            {feedback.deployed && (
              <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                feedback.success
                  ? 'bg-green-50 text-green-700'
                  : 'bg-red-50 text-red-700'
              }`}>
                {feedback.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
                {feedback.success ? 'Successful' : 'Had Issues'}
              </span>
            )}
          </div>
        </div>

        {/* Rating */}
        <div className="flex items-center gap-1 ml-4">
          {[1, 2, 3, 4, 5].map((star) => (
            <Star
              key={star}
              size={16}
              className={star <= feedback.satisfaction_rating
                ? 'text-amber-400 fill-amber-400'
                : 'text-slate-200'
              }
            />
          ))}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
          {feedback.issues_encountered && feedback.issues_encountered.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-red-700 mb-1">Issues Encountered:</h4>
              <ul className="list-disc list-inside text-sm text-slate-600">
                {feedback.issues_encountered.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {feedback.modifications_made && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-1">Modifications Made:</h4>
              <p className="text-sm text-slate-600">{feedback.modifications_made}</p>
            </div>
          )}

          {feedback.comments && (
            <div>
              <h4 className="text-sm font-semibold text-slate-700 mb-1">Comments:</h4>
              <p className="text-sm text-slate-600">{feedback.comments}</p>
            </div>
          )}

          <div className="text-xs text-slate-400">
            Design ID: {feedback.design_id}
          </div>
        </div>
      )}
    </div>
  );
}
