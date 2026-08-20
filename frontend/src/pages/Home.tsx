import { useEffect, useState } from 'react'
import { fetchHealth } from '../api/client'

export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')

  useEffect(() => {
    fetchHealth()
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus('unavailable'))
  }, [])

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-3xl font-bold text-gray-900">
        역량 기반 채용공고 매칭
      </h1>
      <p className="text-gray-600">
        JD 본문의 요구 역량과 내 역량을 대조해 공고를 찾아주는 서비스
      </p>
      <p className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-700">
        Backend API: <span className="font-mono">{apiStatus}</span>
      </p>
    </main>
  )
}
