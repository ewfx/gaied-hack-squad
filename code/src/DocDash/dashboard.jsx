import React, { useState } from 'react';
import { AlertCircle, CheckCircle, FileText, Mail, ChevronRight, Upload, Inbox, FileDown, ArrowRightCircle, Settings, Filter, Clock } from 'lucide-react';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');

  // Sample data for demonstration
  const stats = {
    documentsProcessed: 247,
    emailsTriaged: 183,
    validationRules: 56,
    pendingReview: 12,
    automatedFixes: 143
  };

  const recentDocuments = [
    { id: 1, name: 'Quarterly Compliance Report.pdf', type: 'Regulatory', priority: 'High', status: 'Validated', timestamp: '2025-03-22 09:23:15' },
    { id: 2, name: 'Customer Data Breach Report.docx', type: 'Incident', priority: 'Critical', status: 'Needs Review', timestamp: '2025-03-22 11:47:32' },
    { id: 3, name: 'Annual Risk Assessment.xlsx', type: 'Financial', priority: 'Medium', status: 'Processing', timestamp: '2025-03-21 16:08:45' },
    { id: 4, name: 'GDPR Regulatory Update.pdf', type: 'Regulatory', priority: 'High', status: 'Routed', timestamp: '2025-03-21 14:30:11' },
    { id: 5, name: 'Transaction Error Log.csv', type: 'Error Report', priority: 'Medium', status: 'Validated', timestamp: '2025-03-21 10:15:27' }
  ];

  const validationIssues = [
    { id: 1, rule: 'Customer ID Format', severity: 'High', affectedDocs: 3, status: 'Remediated', timestamp: '2025-03-22 08:45:12' },
    { id: 2, rule: 'Transaction Amount Range', severity: 'Critical', affectedDocs: 7, status: 'Pending Review', timestamp: '2025-03-22 09:23:05' },
    { id: 3, rule: 'Missing Required Fields', severity: 'Medium', affectedDocs: 12, status: 'Remediated', timestamp: '2025-03-21 15:37:41' },
    { id: 4, rule: 'Date Format Inconsistency', severity: 'Low', affectedDocs: 28, status: 'Automated Fix', timestamp: '2025-03-21 11:52:18' },
    { id: 5, rule: 'Cross-validation Failure', severity: 'High', affectedDocs: 4, status: 'Manual Review', timestamp: '2025-03-20 16:20:33' }
  ];

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'validated':
      case 'remediated':
      case 'automated fix':
        return 'bg-green-100 text-green-800';
      case 'needs review':
      case 'pending review':
      case 'manual review':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
      case 'routed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-indigo-800 text-white">
        <div className="p-4">
          <h1 className="text-xl font-bold">AI Orchestrator</h1>
          <p className="text-xs text-indigo-200 mt-1">Data Profiling & Routing</p>
        </div>

        <nav className="mt-6">
          <a
            href="#overview"
            onClick={() => setActiveTab('overview')}
            className={`flex items-center px-4 py-3 ${activeTab === 'overview' ? 'bg-indigo-900' : 'hover:bg-indigo-700'}`}
          >
            <Inbox className="w-5 h-5 mr-3" />
            <span>Overview</span>
          </a>

          <a
            href="#documents"
            onClick={() => setActiveTab('documents')}
            className={`flex items-center px-4 py-3 ${activeTab === 'documents' ? 'bg-indigo-900' : 'hover:bg-indigo-700'}`}
          >
            <FileText className="w-5 h-5 mr-3" />
            <span>Documents</span>
          </a>

          <a
            href="#emails"
            onClick={() => setActiveTab('emails')}
            className={`flex items-center px-4 py-3 ${activeTab === 'emails' ? 'bg-indigo-900' : 'hover:bg-indigo-700'}`}
          >
            <Mail className="w-5 h-5 mr-3" />
            <span>Emails</span>
          </a>

          <a
            href="#validation"
            onClick={() => setActiveTab('validation')}
            className={`flex items-center px-4 py-3 ${activeTab === 'validation' ? 'bg-indigo-900' : 'hover:bg-indigo-700'}`}
          >
            <CheckCircle className="w-5 h-5 mr-3" />
            <span>Validation</span>
          </a>

          <a
            href="#settings"
            onClick={() => setActiveTab('settings')}
            className={`flex items-center px-4 py-3 ${activeTab === 'settings' ? 'bg-indigo-900' : 'hover:bg-indigo-700'}`}
          >
            <Settings className="w-5 h-5 mr-3" />
            <span>Settings</span>
          </a>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && (
          <div className="p-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Dashboard Overview</h2>
              <div className="flex space-x-4">
                <button className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Documents
                </button>
                <button className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md flex items-center">
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                </button>
              </div>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Documents Processed</p>
                    <h3 className="text-2xl font-bold text-gray-800">{stats.documentsProcessed}</h3>
                  </div>
                  <div className="p-3 rounded-full bg-indigo-100 text-indigo-600">
                    <FileText className="w-6 h-6" />
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Emails Triaged</p>
                    <h3 className="text-2xl font-bold text-gray-800">{stats.emailsTriaged}</h3>
                  </div>
                  <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                    <Mail className="w-6 h-6" />
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Validation Rules</p>
                    <h3 className="text-2xl font-bold text-gray-800">{stats.validationRules}</h3>
                  </div>
                  <div className="p-3 rounded-full bg-green-100 text-green-600">
                    <CheckCircle className="w-6 h-6" />
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Pending Review</p>
                    <h3 className="text-2xl font-bold text-gray-800">{stats.pendingReview}</h3>
                  </div>
                  <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                    <Clock className="w-6 h-6" />
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Automated Fixes</p>
                    <h3 className="text-2xl font-bold text-gray-800">{stats.automatedFixes}</h3>
                  </div>
                  <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                    <ArrowRightCircle className="w-6 h-6" />
                  </div>
                </div>
              </div>
            </div>

            {/* Recent documents */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8">
              <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-semibold text-gray-800">Recent Documents</h3>
                <a href="#" className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center">
                  View All
                  <ChevronRight className="w-4 h-4 ml-1" />
                </a>
              </div>
              <div className="divide-y divide-gray-100">
                {recentDocuments.map(doc => (
                  <div key={doc.id} className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="p-2 rounded-md bg-gray-100 mr-4">
                        <FileText className="w-5 h-5 text-gray-500" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-800">{doc.name}</h4>
                        <p className="text-xs text-gray-500">{doc.timestamp}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(doc.status)}`}>
                        {doc.status}
                      </span>
                      <button className="text-gray-400 hover:text-indigo-600">
                        <ArrowRightCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Validation Issues */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-100">
              <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-semibold text-gray-800">Recent Validation Issues</h3>
                <a href="#" className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center">
                  View All
                  <ChevronRight className="w-4 h-4 ml-1" />
                </a>
              </div>
              <div className="divide-y divide-gray-100">
                {validationIssues.map(issue => (
                  <div key={issue.id} className="px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="p-2 rounded-md bg-red-50 mr-4">
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-800">{issue.rule}</h4>
                        <p className="text-xs text-gray-500">{issue.timestamp}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${getSeverityColor(issue.severity)}`}>
                        {issue.severity}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(issue.status)}`}>
                        {issue.status}
                      </span>
                      <button className="text-gray-400 hover:text-indigo-600">
                        <ArrowRightCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'validation' && (
          <div className="p-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Validation Rules & Issues</h2>
              <div className="flex space-x-4">
                <button className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center">
                  <FileDown className="w-4 h-4 mr-2" />
                  Export Report
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="font-semibold text-gray-800">Active Validation Rules</h3>
              </div>
              <div className="p-6">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rule ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Field(s)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">VR-001</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Customer ID must be 10 digits</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">customer_id</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Format Check</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800">High</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <a href="#" className="text-indigo-600 hover:text-indigo-900">Edit</a>
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">VR-002</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Transaction amount must be positive</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">amount</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Range Check</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">Critical</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <a href="#" className="text-indigo-600 hover:text-indigo-900">Edit</a>
                      </td>
                    </tr>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">VR-003</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Required fields must not be empty</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">name, email, address</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Not Null Check</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">Medium</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <a href="#" className="text-indigo-600 hover:text-indigo-900">Edit</a>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg shadow-sm border border-gray-100">
                <div className="px-6 py-4 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-800">Validation Status</h3>
                </div>
                <div className="p-6">
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm text-gray-500">Total Rules</div>
                      <div className="font-medium text-gray-900">56</div>
                    </div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm text-gray-500">Passing</div>
                      <div className="font-medium text-green-600">42 (75%)</div>
                    </div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm text-gray-500">Failed</div>
                      <div className="font-medium text-red-600">14 (25%)</div>
                    </div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm text-gray-500">Automated Fixes</div>
                      <div className="font-medium text-gray-900">9</div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-500">Manual Review Required</div>
                      <div className="font-medium text-gray-900">5</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-100">
                <div className="px-6 py-4 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-800">Recent Remediation Actions</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="p-4 bg-green-50 rounded-md border border-green-100">
                      <div className="flex items-center">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                        <h4 className="text-sm font-medium text-gray-800">Auto-fixed: Date Format Standardization</h4>
                      </div>
                      <p className="mt-2 text-xs text-gray-500">28 records updated to ISO date format</p>
                      <p className="mt-1 text-xs text-gray-400">2025-03-21 11:52:18</p>
                    </div>

                    <div className="p-4 bg-green-50 rounded-