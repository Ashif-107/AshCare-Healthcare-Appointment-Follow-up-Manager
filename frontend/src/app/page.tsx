import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="max-w-4xl w-full bg-white rounded-3xl shadow-xl overflow-hidden p-10 space-y-8 text-center transition-all hover:shadow-2xl">
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
          AshCare
        </h1>
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
          Healthcare Appointment & Follow-up Manager
        </h1>
        <p className="text-xl text-gray-600 font-medium">
          Book appointments, share symptoms securely, and get AI-powered visit summaries.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
          <Link href="/patient/book" className="group block p-6 bg-blue-50 rounded-2xl hover:bg-blue-600 transition-colors duration-300">
            <h2 className="text-2xl font-bold text-blue-800 group-hover:text-white mb-2">For Patients</h2>
            <p className="text-blue-600 group-hover:text-blue-100">Find a doctor and book your slot easily.</p>
          </Link>

          <Link href="/doctor/dashboard" className="group block p-6 bg-indigo-50 rounded-2xl hover:bg-indigo-600 transition-colors duration-300">
            <h2 className="text-2xl font-bold text-indigo-800 group-hover:text-white mb-2">For Doctors</h2>
            <p className="text-indigo-600 group-hover:text-indigo-100">Manage appointments and submit notes.</p>
          </Link>

          <Link href="/admin/dashboard" className="group block p-6 bg-purple-50 rounded-2xl hover:bg-purple-600 transition-colors duration-300">
            <h2 className="text-2xl font-bold text-purple-800 group-hover:text-white mb-2">For Admins</h2>
            <p className="text-purple-600 group-hover:text-purple-100">Manage doctor leaves and system settings.</p>
          </Link>
        </div>
      </div>

      <p className="mt-12 text-gray-400 text-sm text-center gap-10">
        Made By Ashif <br></br>
        Powered by Next.js, FastAPI, SQLModel, and Groq LLM
      </p>
    </div>
  );
}
