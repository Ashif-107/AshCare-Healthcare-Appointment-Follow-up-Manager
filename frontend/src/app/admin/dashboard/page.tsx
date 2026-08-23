"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminDashboard() {
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState("");
  const [leaveDate, setLeaveDate] = useState("");
  const [message, setMessage] = useState("");
  const [createMsg, setCreateMsg] = useState("");
  const [userName, setUserName] = useState("");
  
  // New doctor fields
  const [docEmail, setDocEmail] = useState("");
  const [docPassword, setDocPassword] = useState("");
  const [docName, setDocName] = useState("");
  const [docSpec, setDocSpec] = useState("");

  const router = useRouter();

  const fetchDoctors = () => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/doctors/`)
      .then(res => res.json())
      .then(data => setDoctors(data));
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    
    if (!token || role !== "ADMIN") {
      router.push("/auth/login");
      return;
    }

    setUserName(localStorage.getItem("fullName") || "Admin");

    fetchDoctors();
  }, [router]);

  const handleMarkLeave = async () => {
    if (!selectedDoctor || !leaveDate) return;
    
    const token = localStorage.getItem("token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/admin/leaves`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` 
      },
      body: JSON.stringify({ doctor_id: Number(selectedDoctor), leave_date: leaveDate, reason: "Admin requested" })
    });
    
    const data = await res.json();
    if (res.ok) {
      setMessage(`Success! Cancelled ${data.affected_appointments_cancelled} overlapping appointments and queued notification emails.`);
    } else {
      setMessage(`Error: ${data.detail || 'Failed to mark leave'}`);
    }
  };

  const handleCreateDoctor = async (e: any) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/admin/doctors`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ email: docEmail, password: docPassword, full_name: docName, specialization: docSpec })
    });
    
    if (res.ok) {
      setCreateMsg("Doctor created successfully!");
      setDocEmail(""); setDocPassword(""); setDocName(""); setDocSpec("");
      fetchDoctors(); // Refresh list
    } else {
      const data = await res.json();
      setCreateMsg(`Error: ${data.detail || 'Failed to create doctor'}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-800">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex justify-between items-end">
          <h1 className="text-4xl font-bold text-purple-800">Admin Dashboard</h1>
          <p className="text-lg font-medium text-gray-600">Welcome, {userName}</p>
        </div>
        
        <div className="bg-white p-6 rounded-2xl shadow">
          <h2 className="text-2xl font-semibold mb-4 text-purple-600">Register New Doctor</h2>
          {createMsg && <div className="p-4 mb-4 bg-purple-100 text-purple-800 rounded-xl">{createMsg}</div>}
          <form onSubmit={handleCreateDoctor} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                <input type="text" required value={docName} onChange={e => setDocName(e.target.value)}
                  className="mt-1 block w-full p-2 border border-gray-300 rounded-lg text-black" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Specialization</label>
                <input type="text" required value={docSpec} onChange={e => setDocSpec(e.target.value)}
                  className="mt-1 block w-full p-2 border border-gray-300 rounded-lg text-black" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" required value={docEmail} onChange={e => setDocEmail(e.target.value)}
                  className="mt-1 block w-full p-2 border border-gray-300 rounded-lg text-black" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Password</label>
                <input type="password" required value={docPassword} onChange={e => setDocPassword(e.target.value)}
                  className="mt-1 block w-full p-2 border border-gray-300 rounded-lg text-black" />
              </div>
            </div>
            <button type="submit" className="bg-purple-600 text-white font-bold py-2 px-6 rounded-xl hover:bg-purple-700 transition">
              Create Doctor
            </button>
          </form>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow">
          <h2 className="text-2xl font-semibold mb-4 text-purple-600">Manage Doctor Leaves</h2>
          <p className="text-sm text-gray-600 mb-6">Marking a doctor on leave will automatically cancel any existing appointments for that day and notify the patients.</p>
          
          {message && <div className="p-4 mb-6 bg-purple-100 text-purple-800 rounded-xl">{message}</div>}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Doctor</label>
              <select value={selectedDoctor} onChange={e => setSelectedDoctor(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-xl text-black">
                <option value="">-- Choose a Doctor --</option>
                {doctors.map((doc: any) => (
                  <option key={doc.id} value={doc.id}>{doc.full_name} ({doc.specialization})</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Leave Date</label>
              <input type="date" value={leaveDate} onChange={e => setLeaveDate(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-xl text-black" />
            </div>
            
            <button onClick={handleMarkLeave} className="bg-purple-600 text-white font-bold py-3 px-6 rounded-xl hover:bg-purple-700 transition">
              Mark Leave & Resolve Conflicts
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
