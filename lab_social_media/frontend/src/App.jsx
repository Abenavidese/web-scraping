import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend, LineChart, Line
} from 'recharts'
import {
  Terminal, Play, Activity, Database, MessageSquare,
  TrendingUp, Search, Cpu, Globe, Filter, ChevronDown, ChevronUp
} from 'lucide-react'
import './index.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [postsLimit, setPostsLimit] = useState(10)
  const [commentsLimit, setCommentsLimit] = useState(5)
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState([])
  const [results, setResults] = useState(null)
  const [selectedNetwork, setSelectedNetwork] = useState('all')
  const [expandedSections, setExpandedSections] = useState({
    comments: true,
    charts: true
  })

  const logsEndRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/logs')

    ws.onmessage = (event) => {
      const msg = event.data
      setLogs(prev => [...prev, msg])

      if (logsEndRef.current) {
        logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
      }

      if (msg.includes("Process finished")) {
        setStatus('completed')
        setTimeout(fetchResults, 1000)
      }
    }

    return () => ws.close()
  }, [])

  const fetchResults = async () => {
    try {
      const res = await axios.get(`${API_URL}/results`)
      setResults(res.data)
    } catch (e) {
      console.error("Failed to fetch results", e)
    }
  }

  const startScraping = async () => {
    if (!query) return alert("Please enter a search topic")

    setStatus('running')
    setLogs([])
    setResults(null)

    try {
      await axios.post(`${API_URL}/start-scraping`, {
        query,
        posts: parseInt(postsLimit),
        comments: parseInt(commentsLimit)
      })
    } catch (e) {
      console.error(e)
      setStatus('idle')
      alert("Error starting scraper")
    }
  }

  const getChartData = () => {
    if (!results || !results.summary) return []
    const sent = results.summary.global_sentiment
    return [
      { name: 'Positivo', value: sent.positive, color: '#00ff41' },
      { name: 'Neutro', value: sent.neutral, color: '#ffff00' },
      { name: 'Negativo', value: sent.negative, color: '#ff0055' }
    ]
  }

  const getNetworkData = () => {
    if (!results || !results.networks) return []
    return Object.entries(results.networks).map(([name, data]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      items: Array.isArray(data) ? data.length : 0
    }))
  }

  const getAllComments = () => {
    if (!results || !results.networks) return []
    let comments = []

    Object.entries(results.networks).forEach(([network, data]) => {
      if (Array.isArray(data)) {
        data.forEach((item, idx) => {
          // Handle different data structures
          const text = item.text || item.content || item.caption_snippet || item.comment || ''
          const sentiment = item.sentiment || item.sentiment_deepseek || 'NEUTRAL'
          const reasoning = item.reasoning || item.explanation_deepseek || ''

          if (text && (selectedNetwork === 'all' || selectedNetwork === network)) {
            comments.push({
              network: network.charAt(0).toUpperCase() + network.slice(1),
              text: text.substring(0, 200),
              sentiment: sentiment.toUpperCase(),
              reasoning: reasoning.substring(0, 150),
              id: `${network}-${idx}`
            })
          }
        })
      }
    })

    return comments
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  return (
    <div className="min-h-screen p-8 flex flex-col gap-8">

      {/* HEADER */}
      <motion.header
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass-panel p-6"
      >
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold neon-glow flex items-center gap-3" style={{ color: 'var(--neon-green)' }}>
              <Activity /> SOCIAL PULSE NEXUS
            </h1>
            <p className="text-dim text-sm mt-1" style={{ fontFamily: 'monospace' }}>
              &gt; Advanced Parallel Intelligence Platform v2.0
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`px-3 py-1 rounded-full text-xs font-bold border ${status === 'running'
                ? 'border-yellow-400 text-yellow-400'
                : 'border-green-400 text-green-400'
              }`} style={{
                animation: status === 'running' ? 'pulse 1s infinite' : 'none'
              }}>
              {status === 'running' ? '● PROCESSING' : '● READY'}
            </div>
          </div>
        </div>
      </motion.header>

      {/* MAIN CONTROL GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* LEFT: Controls */}
        <motion.div
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-6 flex flex-col gap-6"
        >
          <h2 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--neon-green)' }}>
            <Search size={20} /> MISSION PARAMETERS
          </h2>

          <div className="flex flex-col gap-2">
            <label className="text-xs uppercase text-dim">Search Query</label>
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="e.g. Artificial Intelligence"
              className="input-glass text-lg"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase text-dim">Max Posts</label>
              <input
                type="number"
                value={postsLimit}
                onChange={e => setPostsLimit(e.target.value)}
                className="input-glass"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase text-dim">Comments/Post</label>
              <input
                type="number"
                value={commentsLimit}
                onChange={e => setCommentsLimit(e.target.value)}
                className="input-glass"
              />
            </div>
          </div>

          <button
            onClick={startScraping}
            disabled={status === 'running'}
            className={`btn-primary mt-auto flex justify-center items-center gap-2 ${status === 'running' ? 'btn-disabled' : ''
              }`}
          >
            {status === 'running' ? <Cpu className="animate-spin" /> : <Play size={18} />}
            {status === 'running' ? 'PROCESSING...' : 'INITIATE SCAN'}
          </button>
        </motion.div>

        {/* MIDDLE & RIGHT: Terminal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-panel p-0 overflow-hidden flex flex-col lg:col-span-2 relative terminal-scan"
          style={{
            background: '#000',
            minHeight: '400px',
            maxHeight: '400px'
          }}
        >
          <div className="px-4 py-2 flex items-center justify-between border-b"
            style={{ background: '#0a1a0a', borderColor: 'var(--neon-green)' }}>
            <span className="text-xs font-mono flex items-center gap-2" style={{ color: 'var(--neon-green)' }}>
              <Terminal size={12} /> LIVE_EXECUTION_LOG.sys
            </span>
            <span className="text-xs" style={{ color: 'var(--text-dim)' }}>
              {logs.length} lines
            </span>
          </div>
          <div className="p-4 font-mono text-xs overflow-y-auto flex-1 space-y-1"
            style={{ color: 'var(--neon-green)' }}>
            {logs.length === 0 && (
              <span style={{ opacity: 0.5 }}>
                &gt; Awaiting command inputs...
              </span>
            )}
            {logs.map((log, i) => (
              <div key={i} className="border-b pb-0.5"
                style={{ borderColor: 'rgba(0,255,65,0.1)' }}>
                <span style={{ color: 'var(--text-dim)', marginRight: '8px' }}>
                  [{new Date().toLocaleTimeString()}]
                </span>
                {log}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </motion.div>
      </div>

      {/* RESULTS SECTION */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex flex-col gap-8"
          >
            {/* KPI ROW */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <KpiCard
                title="Total Extracted"
                value={results.summary?.total_items_processed || 0}
                icon={<Database />}
              />
              <KpiCard
                title="Execution Time"
                value={`${results.summary?.parallel_execution?.total_time || 0}s`}
                icon={<TrendingUp />}
              />
              <KpiCard
                title="Positive Sentiment"
                value={`${results.summary?.global_sentiment?.positive || 0}`}
                icon={<MessageSquare />}
              />
              <KpiCard
                title="Speedup Factor"
                value={`${results.summary?.parallel_execution?.speedup || 0}x`}
                icon={<Cpu />}
              />
            </div>

            {/* CHARTS SECTION */}
            <div className="glass-panel p-6">
              <div
                className="flex justify-between items-center cursor-pointer mb-4"
                onClick={() => toggleSection('charts')}
              >
                <h3 className="text-lg font-bold" style={{ color: 'var(--neon-green)' }}>
                  DATA VISUALIZATION
                </h3>
                {expandedSections.charts ? <ChevronUp /> : <ChevronDown />}
              </div>

              {expandedSections.charts && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Sentiment Distribution */}
                  <div>
                    <h4 className="text-sm uppercase mb-4" style={{ color: 'var(--text-dim)' }}>
                      Sentiment Distribution
                    </h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={getChartData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {getChartData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            background: '#0a0e0a',
                            border: '1px solid var(--neon-green)',
                            color: 'var(--neon-green)'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Network Distribution */}
                  <div>
                    <h4 className="text-sm uppercase mb-4" style={{ color: 'var(--text-dim)' }}>
                      Items per Network
                    </h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={getNetworkData()}>
                        <XAxis
                          dataKey="name"
                          stroke="var(--neon-green)"
                        />
                        <YAxis stroke="var(--neon-green)" />
                        <Tooltip
                          contentStyle={{
                            background: '#0a0e0a',
                            border: '1px solid var(--neon-green)',
                            color: 'var(--neon-green)'
                          }}
                        />
                        <Bar dataKey="items" fill="var(--neon-green)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

            {/* COMMENTS TABLE */}
            <div className="glass-panel p-6">
              <div
                className="flex justify-between items-center cursor-pointer mb-4"
                onClick={() => toggleSection('comments')}
              >
                <h3 className="text-lg font-bold flex items-center gap-2" style={{ color: 'var(--neon-green)' }}>
                  <MessageSquare size={20} /> EXTRACTED COMMENTS ({getAllComments().length})
                </h3>
                {expandedSections.comments ? <ChevronUp /> : <ChevronDown />}
              </div>

              {expandedSections.comments && (
                <>
                  {/* Filter */}
                  <div className="mb-4 flex items-center gap-4">
                    <Filter size={16} style={{ color: 'var(--text-dim)' }} />
                    <select
                      value={selectedNetwork}
                      onChange={(e) => setSelectedNetwork(e.target.value)}
                      className="input-glass"
                      style={{ width: '200px' }}
                    >
                      <option value="all">All Networks</option>
                      <option value="twitter">Twitter</option>
                      <option value="facebook">Facebook</option>
                      <option value="instagram">Instagram</option>
                      <option value="linkedin">LinkedIn</option>
                    </select>
                  </div>

                  {/* Table */}
                  <div className="overflow-x-auto">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th style={{ width: '100px' }}>Network</th>
                          <th>Text</th>
                          <th style={{ width: '120px' }}>Sentiment</th>
                          <th style={{ width: '200px' }}>Reasoning</th>
                        </tr>
                      </thead>
                      <tbody>
                        {getAllComments().map((comment) => (
                          <tr key={comment.id}>
                            <td>
                              <span className="badge" style={{
                                background: 'rgba(0,255,65,0.1)',
                                color: 'var(--neon-green)',
                                border: '1px solid var(--neon-green)'
                              }}>
                                {comment.network}
                              </span>
                            </td>
                            <td style={{ maxWidth: '400px' }}>{comment.text}</td>
                            <td>
                              <span className={`badge ${comment.sentiment.includes('POSITIV') ? 'badge-positive' :
                                  comment.sentiment.includes('NEGATIV') ? 'badge-negative' :
                                    'badge-neutral'
                                }`}>
                                {comment.sentiment}
                              </span>
                            </td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                              {comment.reasoning || 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>

            {/* STORYTELLING */}
            <div className="glass-panel p-6">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: 'var(--neon-green)' }}>
                <Globe size={18} /> GLOBAL NARRATIVE ANALYSIS
              </h3>
              <div className="text-sm leading-relaxed space-y-4" style={{ color: 'var(--text-main)' }}>
                <p className="border-l-2 pl-4" style={{ borderColor: 'var(--neon-green)' }}>
                  <strong>Executive Summary:</strong> The query "{results.summary?.query}" generated a total of{' '}
                  <span style={{ color: 'var(--neon-green)' }}>{results.summary?.total_items_processed}</span> data points across{' '}
                  <span style={{ color: 'var(--neon-green)' }}>{Object.keys(results.networks).length}</span> networks.
                </p>
                <p>
                  The prevailing sentiment is <strong style={{ color: 'var(--neon-green)' }}>
                    {results.summary?.global_sentiment?.positive > results.summary?.global_sentiment?.negative
                      ? 'POSITIVE' : 'NEGATIVE'}
                  </strong> with {results.summary?.global_sentiment?.positive} positive interactions compared to{' '}
                  {results.summary?.global_sentiment?.negative} negative ones.
                </p>

                <div className="mt-6 p-4 rounded border" style={{
                  background: 'rgba(0,255,65,0.05)',
                  borderColor: 'var(--neon-green)'
                }}>
                  <h4 className="text-xs uppercase mb-2" style={{ color: 'var(--text-dim)' }}>
                    DeepSeek LLM Performance
                  </h4>
                  <p style={{ color: 'var(--neon-green)', fontStyle: 'italic' }}>
                    "The concurrency efficiency reached {results.summary?.parallel_execution?.efficiency}%,
                    demonstrating high throughput in data ingestion. Speedup factor: {results.summary?.parallel_execution?.speedup}x"
                  </p>
                </div>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}

function KpiCard({ title, value, icon }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="glass-panel p-4 flex items-center justify-between"
    >
      <div>
        <p className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-dim)' }}>
          {title}
        </p>
        <p className="text-2xl font-bold mt-1 neon-glow" style={{ color: 'var(--neon-green)' }}>
          {value}
        </p>
      </div>
      <div className="p-3 rounded-full" style={{
        background: 'rgba(0,255,65,0.1)',
        color: 'var(--neon-green)'
      }}>
        {icon}
      </div>
    </motion.div>
  )
}

export default App
