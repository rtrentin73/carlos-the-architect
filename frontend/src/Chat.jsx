const [designDoc, setDesignDoc] = useState("");

const startDesign = async (reqs) => {
  setDesignDoc(""); // Clear previous
  const response = await fetch("/design", {
    method: "POST",
    body: JSON.stringify({ requirements: reqs }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");
    
    lines.forEach(line => {
        if (line.startsWith("data: ") && !line.includes("[DONE]")) {
            const data = JSON.parse(line.replace("data: ", ""));
            setDesignDoc((prev) => prev + data.token);
        }
    });
  }
};
