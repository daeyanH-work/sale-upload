import UploadForm from "./components/UploadForm";
import "./App.css";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>📊 Sale Upload Portal</h1>
        <p>Upload your sales file, select a client &amp; date, and download the processed CSV.</p>
      </header>
      <main>
        <UploadForm />
      </main>
    </div>
  );
}

export default App;
