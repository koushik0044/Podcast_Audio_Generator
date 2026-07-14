import ScriptGenerator from './components/ScriptGenerator';

function App() {
  return (
    <div className="App">
      <video className="absolute top-0 left-0 w-full h-full object-cover" src="background.mp4" loop autoPlay muted></video>

      {/* Overlay content */}
      <ScriptGenerator />
    </div>
  );
}

export default App;
