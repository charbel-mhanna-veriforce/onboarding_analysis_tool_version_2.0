import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  Upload, FileText, CheckCircle, AlertCircle, Download, RefreshCw,
  Clock, TrendingUp, FileSpreadsheet, History, Settings, BarChart3
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

function App() {
  const terminalRef = useRef(null);

  // Simple file states - NO pre-upload
  const [cbxFile, setCbxFile] = useState(null);
  const [hcFile, setHcFile] = useState(null);
  const [minCompanyRatio, setMinCompanyRatio] = useState(80);
  const [minAddressRatio, setMinAddressRatio] = useState(80);

  // Job states
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState(null);

  // Dashboard states
  const [activeTab, setActiveTab] = useState('upload');
  const [jobHistory, setJobHistory] = useState([]);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({
    totalJobs: 0,
    successfulJobs: 0,
    failedJobs: 0,
    totalRecordsProcessed: 0,
    averageTime: 0
  });

  useEffect(() => {
    const savedHistory = JSON.parse(localStorage.getItem('jobHistory') || '[]');
    setJobHistory(savedHistory);
    updateStats();
  }, []);

  const updateStats = () => {
    const savedHistory = JSON.parse(localStorage.getItem('jobHistory') || '[]');
    const successful = savedHistory.filter(j => j.status === 'completed').length;
    const failed = savedHistory.filter(j => j.status === 'failed').length;
    const avgTime = savedHistory.filter(j => j.processingTime).reduce((sum, j) => sum + j.processingTime, 0) / (successful || 1);

    setStats({
      totalJobs: savedHistory.length,
      successfulJobs: successful,
      failedJobs: failed,
      totalRecordsProcessed: 0,
      averageTime: avgTime
    });
  };

  const addLog = (message, type = 'info') => {
    setLogs(prev => [{
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      message,
      type
    }, ...prev]);
  };

  const saveJobToHistory = (job) => {
    const savedHistory = JSON.parse(localStorage.getItem('jobHistory') || '[]');
    const newHistory = [job, ...savedHistory].slice(0, 50);
    localStorage.setItem('jobHistory', JSON.stringify(newHistory));
    setJobHistory(newHistory);
    updateStats();
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    let interval;
    if (startTime && jobStatus?.status === 'processing') {
      interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [startTime, jobStatus?.status]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Simple file selection - NO upload yet
  const handleFileChange = (setter) => (e) => {
    const file = e.target.files[0];
    if (file) {
      setter(file);
      addLog(`File selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`, 'info');
    }
  };

  const pollJobStatus = useCallback(async (id) => {
    try {
      const response = await fetch(`${API_URL}/api/jobs/${id}`);
      if (!response.ok) throw new Error('Failed to fetch status');

      const data = await response.json();
      setJobStatus(data);

      if (data.status === 'processing') {
        setTimeout(() => pollJobStatus(id), 1000);
      } else if (data.status === 'completed') {
        setLoading(false);
        addLog('Job completed!', 'success');
        saveJobToHistory({
          jobId: id,
          status: 'completed',
          cbxFile: cbxFile?.name,
          hcFile: hcFile?.name,
          timestamp: new Date().toISOString(),
          processingTime: elapsedTime,
          resultFile: data.result_file
        });
      } else if (data.status === 'failed') {
        setError(data.error);
        setLoading(false);
        addLog(`Job failed: ${data.error}`, 'error');
        saveJobToHistory({
          jobId: id,
          status: 'failed',
          cbxFile: cbxFile?.name,
          hcFile: hcFile?.name,
          timestamp: new Date().toISOString(),
          processingTime: elapsedTime,
          error: data.error
        });
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
      addLog(`Error: ${err.message}`, 'error');
    }
  }, [elapsedTime, cbxFile, hcFile]);

  // ONE upload when starting job
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!cbxFile || !hcFile) {
      setError('Please select both files');
      addLog('Error: Both files required', 'error');
      return;
    }

    setError(null);
    setLoading(true);
    setElapsedTime(0);
    setStartTime(Date.now());
    setJobStatus({
      job_id: 'uploading',
      status: 'processing',
      progress: 0,
      message: 'Uploading files...',
      created_at: new Date().toISOString()
    });

    addLog(`Uploading CBX: ${cbxFile.name} (${(cbxFile.size / 1024 / 1024).toFixed(2)} MB)`, 'info');
    addLog(`Uploading HC: ${hcFile.name} (${(hcFile.size / 1024 / 1024).toFixed(2)} MB)`, 'info');

    try {
      const formData = new FormData();
      formData.append('cbx_file', cbxFile);
      formData.append('hc_file', hcFile);
      formData.append('min_company_ratio', minCompanyRatio);
      formData.append('min_address_ratio', minAddressRatio);

      const response = await fetch(`${API_URL}/api/match`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus(data);
      addLog(`Job started: ${data.job_id.substring(0, 8)}...`, 'success');
      pollJobStatus(data.job_id);

    } catch (err) {
      setError(err.message);
      setLoading(false);
      setStartTime(null);
      addLog(`Failed: ${err.message}`, 'error');
    }
  };

  const handleDownload = async () => {
    try {
      addLog('Downloading results...', 'info');
      const response = await fetch(`${API_URL}/api/jobs/${jobId}/download`);
      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = jobStatus?.result_file || 'results.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      addLog('Downloaded successfully', 'success');
    } catch (err) {
      addLog(`Download failed: ${err.message}`, 'error');
    }
  };

  const handleReset = () => {
    setCbxFile(null);
    setHcFile(null);
    setJobId(null);
    setJobStatus(null);
    setError(null);
    setLoading(false);
    setElapsedTime(0);
    setStartTime(null);
    addLog('Reset', 'info');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2 rounded-lg">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Contractor Matching System</h1>
                <p className="text-sm text-gray-500">Fast & Simple</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-500">Total Jobs</p>
                <p className="text-xl font-bold text-gray-900">{stats.totalJobs}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Success Rate</p>
                <p className="text-xl font-bold text-green-600">
                  {stats.totalJobs > 0 ? Math.round((stats.successfulJobs / stats.totalJobs) * 100) : 0}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl shadow-sm mb-6 border border-gray-100">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center space-x-2 px-6 py-4 font-medium transition-colors ${
                activeTab === 'upload' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
              }`}
            >
              <Upload className="h-5 w-5" />
              <span>New Upload</span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 px-6 py-4 font-medium transition-colors ${
                activeTab === 'history' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
              }`}
            >
              <History className="h-5 w-5" />
              <span>History</span>
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`flex items-center space-x-2 px-6 py-4 font-medium transition-colors ${
                activeTab === 'logs' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
              }`}
            >
              <FileText className="h-5 w-5" />
              <span>Logs</span>
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'upload' && (
              <div>
                {!jobStatus ? (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-3">CBX Database</label>
                        <div className="relative border-2 border-dashed border-gray-300 rounded-xl p-8 hover:border-blue-400 transition-all bg-white">
                          <input
                            type="file"
                            accept=".csv,.xlsx,.xls"
                            onChange={handleFileChange(setCbxFile)}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                          />
                          <div className="text-center">
                            {cbxFile ? (
                              <CheckCircle className="mx-auto h-12 w-12 text-green-400 mb-3" />
                            ) : (
                              <FileText className="mx-auto h-12 w-12 text-blue-400 mb-3" />
                            )}
                            <p className="text-sm font-medium text-gray-700 mb-1">
                              {cbxFile ? cbxFile.name : 'Click to select CBX file'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {cbxFile ? `${(cbxFile.size / 1024 / 1024).toFixed(2)} MB` : 'CSV, XLSX, or XLS'}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-3">Hiring Client List</label>
                        <div className="relative border-2 border-dashed border-gray-300 rounded-xl p-8 hover:border-blue-400 transition-all bg-white">
                          <input
                            type="file"
                            accept=".csv,.xlsx,.xls"
                            onChange={handleFileChange(setHcFile)}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                          />
                          <div className="text-center">
                            {hcFile ? (
                              <CheckCircle className="mx-auto h-12 w-12 text-green-400 mb-3" />
                            ) : (
                              <Upload className="mx-auto h-12 w-12 text-indigo-400 mb-3" />
                            )}
                            <p className="text-sm font-medium text-gray-700 mb-1">
                              {hcFile ? hcFile.name : 'Click to select HC file'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {hcFile ? `${(hcFile.size / 1024 / 1024).toFixed(2)} MB` : 'CSV, XLSX, or XLS'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                      <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                        <Settings className="h-4 w-4 mr-2" />
                        Matching Configuration
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Company Match Threshold: {minCompanyRatio}%
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={minCompanyRatio}
                            onChange={(e) => setMinCompanyRatio(Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Address Match Threshold: {minAddressRatio}%
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={minAddressRatio}
                            onChange={(e) => setMinAddressRatio(Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </div>
                    </div>

                    {error && (
                      <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4 flex items-start">
                        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
                        <div className="text-sm text-red-700">{error}</div>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={loading || !cbxFile || !hcFile}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-xl
                      font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400
                      disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all"
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="h-5 w-5 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <Upload className="h-5 w-5" />
                          <span>Start Matching</span>
                        </>
                      )}
                    </button>
                  </form>
                ) : (
                  <div className="space-y-6">
                    <div className="text-center">
                      {jobStatus.status === 'completed' ? (
                        <CheckCircle className="mx-auto h-20 w-20 text-green-500 mb-4" />
                      ) : jobStatus.status === 'failed' ? (
                        <AlertCircle className="mx-auto h-20 w-20 text-red-500 mb-4" />
                      ) : (
                        <RefreshCw className="mx-auto h-20 w-20 text-blue-500 animate-spin mb-4" />
                      )}
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">
                        {jobStatus.status === 'completed' && 'Complete!'}
                        {jobStatus.status === 'failed' && 'Failed'}
                        {jobStatus.status === 'processing' && 'Processing...'}
                      </h3>
                      <p className="text-gray-600 mb-6">{jobStatus.message}</p>
                    </div>

                    {jobStatus.status === 'processing' && (
                      <>
                        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <Clock className="h-6 w-6 text-blue-600" />
                              <span className="text-lg font-semibold text-gray-700">Time</span>
                            </div>
                            <span className="text-4xl font-bold text-blue-600">{formatTime(elapsedTime)}</span>
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
                            <span>Progress</span>
                            <span>{Math.round((jobStatus.progress || 0) * 100)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-8">
                            <div
                              className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 h-8 rounded-full transition-all"
                              style={{ width: `${(jobStatus.progress || 0) * 100}%` }}
                            />
                          </div>
                        </div>
                      </>
                    )}

                    <div className="flex gap-4">
                      {jobStatus.status === 'completed' && (
                        <button
                          onClick={handleDownload}
                          className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-4 px-6 rounded-xl
                          font-semibold hover:from-green-700 hover:to-emerald-700 flex items-center justify-center space-x-2"
                        >
                          <Download className="h-5 w-5" />
                          <span>Download Results</span>
                        </button>
                      )}
                      <button
                        onClick={handleReset}
                        className="flex-1 bg-gradient-to-r from-gray-600 to-gray-700 text-white py-4 px-6 rounded-xl
                        font-semibold hover:from-gray-700 hover:to-gray-800 flex items-center justify-center space-x-2"
                      >
                        <RefreshCw className="h-5 w-5" />
                        <span>New Match</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'history' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Job History</h3>
                {jobHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <History className="mx-auto h-16 w-16 text-gray-300 mb-4" />
                    <p className="text-gray-500">No history yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {jobHistory.map((job, idx) => (
                      <div key={idx} className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-900">Job #{job.jobId.substring(0, 8)}</h4>
                            <p className="text-sm text-gray-500">{new Date(job.timestamp).toLocaleString()}</p>
                            <p className="text-sm text-gray-600 mt-2">
                              CBX: {job.cbxFile} | HC: {job.hcFile}
                            </p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            job.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {job.status.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'logs' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Logs</h3>
                <div className="space-y-2">
                  {logs.map((log) => (
                    <div key={log.id} className={`p-4 rounded-lg border ${
                      log.type === 'error' ? 'bg-red-50 border-red-200' :
                      log.type === 'success' ? 'bg-green-50 border-green-200' :
                      'bg-blue-50 border-blue-200'
                    }`}>
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{log.message}</p>
                        <span className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;