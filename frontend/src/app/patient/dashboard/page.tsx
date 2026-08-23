"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import Link from "next/link";

export default function PatientDashboard() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [userName, setUserName] = useState("");
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    
    if (!token || role !== "PATIENT") {
      router.push("/auth/login");
    } else {
      setUserName(localStorage.getItem("fullName") || "Patient");
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/appointments/patient/${localStorage.getItem("userId")}`)
        .then(res => res.json())
        .then(data => setAppointments(data));
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-800">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-bold text-blue-800">Patient Dashboard</h1>
            <p className="text-lg font-medium text-gray-600 mt-1">Welcome, {userName}</p>
          </div>
          <Link href="/patient/book" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-xl transition shadow">
            Book New Appointment
          </Link>
        </div>
        
        <div className="space-y-6">
          {appointments.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl shadow text-center">
              <p className="text-gray-500 text-lg">You have no appointments yet.</p>
              <Link href="/patient/book" className="inline-block mt-4 text-blue-600 hover:underline">
                Click here to book your first appointment!
              </Link>
            </div>
          ) : (
            appointments.map((appt) => (
              <div key={appt.appointment_id} className="bg-white p-6 rounded-2xl shadow border-l-4 border-blue-500">
                <div className="flex justify-between items-start mb-4 border-b pb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800">Dr. {appt.doctor_name}</h2>
                    <p className="text-gray-500">
                      {new Date(appt.start_time).toLocaleDateString()} at {new Date(appt.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${appt.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                    {appt.status}
                  </span>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-700">Your Symptoms</h3>
                    <p className="text-gray-600 bg-gray-50 p-3 rounded-lg mt-1">{appt.symptoms}</p>
                  </div>

                  {appt.status === 'COMPLETED' && appt.post_visit_summary && (
                    <div className="mt-6">
                      <h3 className="font-bold text-green-800 text-lg mb-2">Doctor's AI Summary & Instructions</h3>
                      <div className="bg-green-50 border border-green-200 p-5 rounded-xl">
                        <div className="text-green-900 prose prose-sm max-w-none prose-green">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                            {appt.post_visit_summary}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
