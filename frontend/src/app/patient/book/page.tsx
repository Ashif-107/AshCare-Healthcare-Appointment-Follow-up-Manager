"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function PatientBooking() {
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState<number | null>(null);
  const [slots, setSlots] = useState([]);
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [symptoms, setSymptoms] = useState("");
  const [holdId, setHoldId] = useState<number | null>(null);
  const [heldSlotIndex, setHeldSlotIndex] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [userName, setUserName] = useState("");
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    
    if (!token || role !== "PATIENT") {
      router.push("/auth/login");
      return;
    }

    setUserName(localStorage.getItem("fullName") || "Patient");

    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/doctors/`)
      .then(res => res.json())
      .then(data => setDoctors(data));
  }, [router]);

  const fetchSlots = async (doctorId: number, targetDate: string) => {
    setSelectedDoctor(doctorId);
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/doctors/${doctorId}/slots?target_date=${targetDate}`);
    const data = await res.json();
    setSlots(data);
  };

  const handleHoldSlot = async (slot: any, idx: number) => {
    setHeldSlotIndex(idx);
    const userId = localStorage.getItem("userId");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/appointments/hold`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doctor_id: selectedDoctor, patient_id: userId, start_time: slot.start_time, end_time: slot.end_time })
    });
    
    if (res.ok) {
      const data = await res.json();
      setHoldId(data.appointment_id);
      setMessage("Slot held! Please fill in your symptoms to confirm.");
    } else {
      setMessage("Failed to hold slot. It might be taken.");
      setHeldSlotIndex(null);
    }
  };

  const handleConfirm = async () => {
    if (!holdId || !symptoms) return;
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/appointments/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ appointment_id: holdId, symptoms })
    });
    
    if (res.ok) {
      setMessage("Appointment confirmed! You'll receive an email and calendar invite shortly.");
      setHoldId(null);
      setHeldSlotIndex(null);
      setSymptoms("");
      fetchSlots(selectedDoctor!, date); // Refresh slots
    } else {
      setMessage("Failed to confirm appointment. Hold might have expired.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-800">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex justify-between items-end">
          <h1 className="text-4xl font-bold text-blue-800">Book an Appointment</h1>
          <p className="text-lg font-medium text-gray-600">Welcome, {userName}</p>
        </div>
        
        {message && <div className="p-4 bg-blue-100 text-blue-800 rounded-xl">{message}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-white p-6 rounded-2xl shadow">
            <h2 className="text-2xl font-semibold mb-4">1. Select a Doctor</h2>
            <div className="space-y-4">
              {doctors.map((doc: any) => (
                <div key={doc.id} onClick={() => fetchSlots(doc.id, date)} 
                  className={`p-4 rounded-xl cursor-pointer border-2 transition ${selectedDoctor === doc.id ? 'border-blue-500 bg-blue-50' : 'border-gray-100 hover:border-blue-200'}`}>
                  <h3 className="font-bold text-lg">{doc.full_name}</h3>
                  <p className="text-sm text-gray-500">{doc.specialization}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow">
            <h2 className="text-2xl font-semibold mb-4">2. Pick a Slot</h2>
            <input type="date" value={date} onChange={(e) => { setDate(e.target.value); if(selectedDoctor) fetchSlots(selectedDoctor, e.target.value); }}
              className="w-full p-2 border rounded-lg mb-4" />
            
            {!selectedDoctor && <p className="text-gray-400">Select a doctor first.</p>}
            
            <div className="grid grid-cols-2 gap-3">
              {slots.map((slot: any, idx) => (
                <button key={idx} disabled={!slot.available || (holdId !== null && heldSlotIndex !== idx)} onClick={() => handleHoldSlot(slot, idx)}
                  className={`p-2 rounded-lg text-sm font-medium transition ${
                    heldSlotIndex === idx
                      ? 'bg-blue-800 text-white border-2 border-black shadow-lg transform scale-105'
                      : !slot.available 
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                        : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}>
                  {new Date(slot.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </button>
              ))}
            </div>
          </div>
        </div>

        {holdId && (
          <div className="bg-white p-6 rounded-2xl shadow mt-8">
            <h2 className="text-2xl font-semibold mb-4 text-indigo-700">3. Confirm Details</h2>
            <p className="text-sm text-gray-600 mb-4">Please describe your symptoms to help the AI generate a pre-visit summary for your doctor.</p>
            <textarea value={symptoms} onChange={e => setSymptoms(e.target.value)} rows={4}
              className="w-full p-3 border border-gray-300 rounded-xl mb-4" placeholder="I have a headache and fever..."></textarea>
            <button onClick={handleConfirm} className="w-full bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 transition">
              Confirm Appointment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
