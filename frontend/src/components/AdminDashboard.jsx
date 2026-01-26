import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Shield, Users, Activity, Download, Search, RefreshCw,
  AlertTriangle, CheckCircle, XCircle, UserPlus, UserMinus,
  Lock, Unlock, ChevronLeft, ChevronRight, Filter, Trash2
} from 'lucide-react';

export default function AdminDashboard() {
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditFilters, setAuditFilters] = useState({
    username: '',
    action_prefix: '',
    severity: '',
    limit: 50,
    offset: 0,
  });

  // Stats state
  const [stats, setStats] = useState(null);
  const [statsDays, setStatsDays] = useState(30);

  // Users state
  const [users, setUsers] = useState([]);

  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  // Check if current user is admin
  if (!user?.is_admin) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <Shield size={64} className="text-red-300 mb-4" />
        <h2 className="text-2xl font-bold text-slate-800 mb-2">Access Denied</h2>
        <p className="text-slate-500">You need admin privileges to access this dashboard.</p>
      </div>
    );
  }

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (auditFilters.username) params.append('username', auditFilters.username);
      if (auditFilters.action_prefix) params.append('action_prefix', auditFilters.action_prefix);
      if (auditFilters.severity) params.append('severity', auditFilters.severity);
      params.append('limit', auditFilters.limit.toString());
      params.append('offset', auditFilters.offset.toString());

      const response = await fetch(`${backendBaseUrl}/admin/audit?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch audit logs');
      const data = await response.json();
      setAuditLogs(data.records || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${backendBaseUrl}/admin/audit/stats?days=${statsDays}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data.stats);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${backendBaseUrl}/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data.users || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (username, action) => {
    try {
      let url, method;
      if (action === 'delete') {
        url = `${backendBaseUrl}/admin/users/${username}`;
        method = 'DELETE';
      } else {
        url = `${backendBaseUrl}/admin/users/${username}/${action}`;
        method = 'POST';
      }

      const response = await fetch(url, {
        method,
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Action failed');
      }

      // Refresh users list
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const exportAuditLogs = async (format) => {
    try {
      const params = new URLSearchParams();
      params.append('format', format);
      if (auditFilters.username) params.append('username', auditFilters.username);
      if (auditFilters.action_prefix) params.append('action_prefix', auditFilters.action_prefix);

      const response = await fetch(`${backendBaseUrl}/admin/audit/export?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_export.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'audit') fetchAuditLogs();
    if (activeTab === 'overview') fetchStats();
    if (activeTab === 'users') fetchUsers();
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'overview') fetchStats();
  }, [statsDays]);

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Shield size={28} className="text-indigo-600" />
        <h2 className="text-2xl font-bold text-slate-800">Admin Dashboard</h2>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-200 mb-6">
        <TabButton
          active={activeTab === 'overview'}
          onClick={() => setActiveTab('overview')}
          icon={<Activity size={16} />}
          label="Overview"
        />
        <TabButton
          active={activeTab === 'audit'}
          onClick={() => setActiveTab('audit')}
          icon={<Shield size={16} />}
          label="Audit Logs"
        />
        <TabButton
          active={activeTab === 'users'}
          onClick={() => setActiveTab('users')}
          icon={<Users size={16} />}
          label="User Management"
        />
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
          <AlertTriangle size={18} />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
            <XCircle size={18} />
          </button>
        </div>
      )}

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <OverviewTab
          stats={stats}
          loading={loading}
          statsDays={statsDays}
          setStatsDays={setStatsDays}
          onRefresh={fetchStats}
        />
      )}

      {/* Audit Logs Tab */}
      {activeTab === 'audit' && (
        <AuditLogsTab
          logs={auditLogs}
          filters={auditFilters}
          setFilters={setAuditFilters}
          loading={loading}
          onRefresh={fetchAuditLogs}
          onExport={exportAuditLogs}
        />
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <UsersTab
          users={users}
          currentUser={user}
          loading={loading}
          onRefresh={fetchUsers}
          onAction={handleUserAction}
        />
      )}
    </div>
  );
}

function TabButton({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition ${
        active
          ? 'border-indigo-500 text-indigo-600'
          : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function OverviewTab({ stats, loading, statsDays, setStatsDays, onRefresh }) {
  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw size={24} className="animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-600">Time period:</span>
          <select
            value={statsDays}
            onChange={(e) => setStatsDays(Number(e.target.value))}
            className="border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800 border rounded-lg hover:bg-slate-50"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Events"
          value={stats?.total_events || 0}
          icon={<Activity size={20} className="text-blue-500" />}
        />
        <StatCard
          label="Unique Users"
          value={stats?.unique_users || 0}
          icon={<Users size={20} className="text-green-500" />}
        />
        <StatCard
          label="Errors"
          value={stats?.error_count || 0}
          icon={<AlertTriangle size={20} className="text-red-500" />}
          warning={stats?.error_count > 0}
        />
        <StatCard
          label="Storage"
          value={stats?.storage || 'N/A'}
          icon={<Shield size={20} className="text-purple-500" />}
          isText
        />
      </div>

      {/* Events by Severity */}
      {stats?.events_by_severity && Object.keys(stats.events_by_severity).length > 0 && (
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-slate-800 mb-4">Events by Severity</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(stats.events_by_severity).map(([severity, count]) => (
              <div
                key={severity}
                className={`p-3 rounded-lg ${getSeverityBg(severity)}`}
              >
                <div className="text-xs uppercase tracking-wide text-slate-600">{severity}</div>
                <div className="text-xl font-bold">{count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Events by Action */}
      {stats?.events_by_action && Object.keys(stats.events_by_action).length > 0 && (
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-slate-800 mb-4">Events by Action Category</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {Object.entries(stats.events_by_action)
              .sort((a, b) => b[1] - a[1])
              .map(([action, count]) => (
                <div key={action} className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 font-mono">{action}</span>
                  <span className="font-semibold text-slate-800">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon, warning, isText }) {
  return (
    <div className={`border rounded-lg p-4 ${warning ? 'border-red-200 bg-red-50' : 'bg-white'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
        {icon}
      </div>
      <div className={`text-2xl font-bold ${warning ? 'text-red-600' : 'text-slate-800'}`}>
        {isText ? value : value.toLocaleString()}
      </div>
    </div>
  );
}

function AuditLogsTab({ logs, filters, setFilters, loading, onRefresh, onExport }) {
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, offset: 0 }));
  };

  const handlePageChange = (direction) => {
    setFilters(prev => ({
      ...prev,
      offset: Math.max(0, prev.offset + (direction * prev.limit))
    }));
  };

  useEffect(() => {
    onRefresh();
  }, [filters.offset]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 p-4 bg-slate-50 rounded-lg">
        <Filter size={16} className="text-slate-500" />
        <input
          type="text"
          placeholder="Username"
          value={filters.username}
          onChange={(e) => handleFilterChange('username', e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm w-32"
        />
        <select
          value={filters.action_prefix}
          onChange={(e) => handleFilterChange('action_prefix', e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All Actions</option>
          <option value="auth.">Authentication</option>
          <option value="design.">Design</option>
          <option value="document.">Documents</option>
          <option value="feedback.">Feedback</option>
          <option value="admin.">Admin</option>
          <option value="cache.">Cache</option>
        </select>
        <select
          value={filters.severity}
          onChange={(e) => handleFilterChange('severity', e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">All Severities</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </select>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          <Search size={14} />
          Search
        </button>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => onExport('json')}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-slate-100"
          >
            <Download size={14} />
            JSON
          </button>
          <button
            onClick={() => onExport('csv')}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-slate-100"
          >
            <Download size={14} />
            CSV
          </button>
        </div>
      </div>

      {/* Logs Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw size={24} className="animate-spin text-slate-400" />
        </div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <Shield size={48} className="mx-auto mb-3 opacity-50" />
          <p>No audit logs found matching your criteria.</p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="px-4 py-3 font-semibold">Timestamp</th>
                  <th className="px-4 py-3 font-semibold">User</th>
                  <th className="px-4 py-3 font-semibold">Action</th>
                  <th className="px-4 py-3 font-semibold">Endpoint</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Severity</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, idx) => (
                  <tr key={log.audit_id || idx} className="border-t hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-medium">{log.username || '-'}</td>
                    <td className="px-4 py-3 font-mono text-xs">{log.action}</td>
                    <td className="px-4 py-3 text-slate-600 font-mono text-xs">{log.endpoint}</td>
                    <td className="px-4 py-3">
                      <StatusBadge code={log.status_code} />
                    </td>
                    <td className="px-4 py-3">
                      <SeverityBadge severity={log.severity} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-600">
          Showing {filters.offset + 1} - {filters.offset + logs.length}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handlePageChange(-1)}
            disabled={filters.offset === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={14} />
            Previous
          </button>
          <button
            onClick={() => handlePageChange(1)}
            disabled={logs.length < filters.limit}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

function UsersTab({ users, currentUser, loading, onRefresh, onAction }) {
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleDelete = (username) => {
    if (deleteConfirm === username) {
      onAction(username, 'delete');
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(username);
      // Auto-clear confirmation after 3 seconds
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw size={24} className="animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-600">{users.length} registered users</span>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800 border rounded-lg hover:bg-slate-50"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-4 py-3 font-semibold">Username</th>
              <th className="px-4 py-3 font-semibold">Email</th>
              <th className="px-4 py-3 font-semibold">Role</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.username} className="border-t hover:bg-slate-50">
                <td className="px-4 py-3 font-medium">
                  {u.username}
                  {u.username === currentUser.username && (
                    <span className="ml-2 text-xs text-indigo-600">(you)</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-600">{u.email || '-'}</td>
                <td className="px-4 py-3">
                  {u.is_admin ? (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                      <Shield size={12} />
                      Admin
                    </span>
                  ) : (
                    <span className="text-slate-500 text-xs">User</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {u.disabled ? (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                      <Lock size={12} />
                      Disabled
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      <CheckCircle size={12} />
                      Active
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {u.username !== currentUser.username && (
                    <div className="flex items-center gap-1">
                      {u.is_admin ? (
                        <button
                          onClick={() => onAction(u.username, 'demote')}
                          className="p-1.5 text-amber-700 hover:bg-amber-50 rounded"
                          title="Remove admin role"
                        >
                          <UserMinus size={16} />
                        </button>
                      ) : (
                        <button
                          onClick={() => onAction(u.username, 'promote')}
                          className="p-1.5 text-indigo-700 hover:bg-indigo-50 rounded"
                          title="Promote to admin"
                        >
                          <UserPlus size={16} />
                        </button>
                      )}
                      {u.disabled ? (
                        <button
                          onClick={() => onAction(u.username, 'enable')}
                          className="p-1.5 text-green-700 hover:bg-green-50 rounded"
                          title="Enable account"
                        >
                          <Unlock size={16} />
                        </button>
                      ) : (
                        <button
                          onClick={() => onAction(u.username, 'disable')}
                          className="p-1.5 text-orange-700 hover:bg-orange-50 rounded"
                          title="Disable account"
                        >
                          <Lock size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(u.username)}
                        className={`p-1.5 rounded ${
                          deleteConfirm === u.username
                            ? 'bg-red-600 text-white'
                            : 'text-red-700 hover:bg-red-50'
                        }`}
                        title={deleteConfirm === u.username ? 'Click again to confirm deletion' : 'Delete user permanently'}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ code }) {
  if (!code) return <span className="text-slate-400">-</span>;

  const colors = code < 300
    ? 'bg-green-100 text-green-700'
    : code < 400
    ? 'bg-blue-100 text-blue-700'
    : code < 500
    ? 'bg-amber-100 text-amber-700'
    : 'bg-red-100 text-red-700';

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors}`}>
      {code}
    </span>
  );
}

function SeverityBadge({ severity }) {
  const colors = {
    info: 'bg-blue-100 text-blue-700',
    warning: 'bg-amber-100 text-amber-700',
    error: 'bg-red-100 text-red-700',
    critical: 'bg-red-200 text-red-800',
  };

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[severity] || 'bg-slate-100 text-slate-700'}`}>
      {severity}
    </span>
  );
}

function getSeverityBg(severity) {
  const colors = {
    info: 'bg-blue-50',
    warning: 'bg-amber-50',
    error: 'bg-red-50',
    critical: 'bg-red-100',
  };
  return colors[severity] || 'bg-slate-50';
}
