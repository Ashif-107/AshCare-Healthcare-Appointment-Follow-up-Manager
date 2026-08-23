"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

export default function DoctorDashboard() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [prescription, setPrescription] = useState("");
  const [summary, setSummary] = useState("");
  const [userName, setUserName] = useState("");
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    
    if (!token || role !== "DOCTOR") {
      router.push("/auth/login");
    } else {
      setUserName(localStorage.getItem("fullName") || "Doctor");
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/appointments/doctor/${localStorage.getItem("userId")}`)
        .then(res => res.json())
        .then(data => setAppointments(data));
    }
  }, [router]);

  const submitNotes = async () => {
    if (!selectedAppt) return;
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/appointments/${selectedAppt}/post-visit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes, prescription })
    });
    
    if (res.ok) {
      const data = await res.json();
      setSummary(data.patient_friendly_summary);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-800">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex justify-between items-end">
          <h1 className="text-4xl font-bold text-indigo-800">Doctor Dashboard</h1>
          <p className="text-lg font-medium text-gray-600">Welcome, {userName}</p>
        </div>
        
        <div className="bg-white p-6 rounded-2xl shadow">
          <h2 className="text-2xl font-semibold mb-4 text-indigo-600">Active Consultations</h2>
          
          {appointments.length === 0 ? (
            <p className="text-gray-500">No active appointments right now.</p>
          ) : (
            <div className="space-y-4 mb-6">
              {appointments.map((appt) => (
                <div key={appt.appointment_id} 
                     className={`p-4 border rounded-xl cursor-pointer transition ${selectedAppt === appt.appointment_id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:bg-gray-50'}`}
                     onClick={() => setSelectedAppt(appt.appointment_id)}>
                  <div className="flex justify-between">
                    <h3 className="font-bold text-indigo-900">Patient ID: {appt.patient_id}</h3>
                    <span className={`text-xs font-bold px-2 py-1 rounded ${appt.urgency_level === 'High' ? 'bg-red-100 text-red-700' : appt.urgency_level === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                      {appt.urgency_level} Urgency
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mt-2 prose prose-sm max-w-none">
                    <strong>AI Pre-Visit Summary:</strong>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{appt.pre_visit_summary}</ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedAppt && (
            <div className="space-y-4 pt-4 border-t border-gray-200">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Notes</label>
                <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={4}
                  className="w-full p-3 border border-gray-300 rounded-xl text-black" placeholder="Patient shows signs of viral infection..."></textarea>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prescription</label>
                <textarea value={prescription} onChange={e => setPrescription(e.target.value)} rows={2}
                  className="w-full p-3 border border-gray-300 rounded-xl text-black" placeholder="Paracetamol 500mg..."></textarea>
              </div>
              
              <button onClick={submitNotes} className="bg-indigo-600 text-white font-bold py-3 px-6 rounded-xl hover:bg-indigo-700 transition">
                Submit & Generate Summary
              </button>
            </div>
          )}
        </div>

        {summary && (
          <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-r-2xl shadow">
            <h3 className="text-lg font-bold text-green-800 mb-2">Patient-Friendly Summary Generated (via LLM):</h3>
            <div className="text-green-700 prose prose-sm max-w-none prose-green">
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{summary}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
