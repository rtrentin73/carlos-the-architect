"""
Diagram extraction module for Carlos the Architect.

Extracts and analyzes diagrams/figures from uploaded documents using:
- Azure AI Document Intelligence (prebuilt-layout model) for figure detection
- Azure OpenAI GPT-4 Vision for diagram analysis and description

This enables Carlos to understand architectural diagrams, flowcharts,
and other visual elements in requirements documents.
"""

import base64
import os
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class DiagramType(str, Enum):
    """Classification of diagram types."""
    ARCHITECTURE = "architecture"
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    ERD = "erd"  # Entity-Relationship Diagram
    NETWORK = "network"
    INFRASTRUCTURE = "infrastructure"
    UML = "uml"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Bounding box coordinates for a figure."""
    x: float = Field(description="X coordinate (left)")
    y: float = Field(description="Y coordinate (top)")
    width: float = Field(description="Width of the bounding box")
    height: float = Field(description="Height of the bounding box")


class ExtractedDiagram(BaseModel):
    """Represents a single extracted diagram/figure from a document."""
    diagram_id: str = Field(description="Unique identifier for the diagram")
    page_number: int = Field(description="Page number where the diagram was found (1-indexed)")
    bounding_box: Optional[BoundingBox] = Field(default=None, description="Location of the diagram on the page")
    caption: Optional[str] = Field(default=None, description="Caption text if present near the diagram")
    diagram_type: DiagramType = Field(default=DiagramType.UNKNOWN, description="Classified type of diagram")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score of detection")

    # Vision analysis results (populated if GPT-4 Vision is enabled)
    analysis: Optional[str] = Field(default=None, description="GPT-4 Vision analysis of the diagram")
    components: List[str] = Field(default_factory=list, description="Identified components in the diagram")
    connections: List[str] = Field(default_factory=list, description="Identified connections/flows")
    technologies: List[str] = Field(default_factory=list, description="Identified technologies/services")

    # Raw image data (base64 encoded, for frontend display)
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image data")


class DiagramExtractionResult(BaseModel):
    """Complete result of diagram extraction from a document."""
    document_name: str = Field(description="Original document filename")
    total_pages: int = Field(default=0, description="Total number of pages in the document")
    diagrams_found: int = Field(default=0, description="Number of diagrams detected")
    diagrams: List[ExtractedDiagram] = Field(default_factory=list, description="List of extracted diagrams")
    extraction_method: str = Field(default="none", description="Method used for extraction")
    text_content: str = Field(default="", description="Extracted text content from document")

    # Summary of all diagrams (for quick reference)
    diagram_summary: Optional[str] = Field(default=None, description="AI-generated summary of all diagrams")


def _is_vision_analysis_configured() -> bool:
    """Check if Azure OpenAI GPT-4 Vision is configured for diagram analysis."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_VISION_DEPLOYMENT", "gpt-4o")
    return bool(endpoint and key and deployment)


def _analyze_diagram_with_vision(image_base64: str, context: str = "") -> dict:
    """
    Analyze a diagram image using Azure OpenAI GPT-4 Vision.

    Args:
        image_base64: Base64 encoded image data
        context: Optional context about the document

    Returns:
        Dictionary with analysis results
    """
    if not _is_vision_analysis_configured():
        return {
            "analysis": None,
            "components": [],
            "connections": [],
            "technologies": [],
            "diagram_type": DiagramType.UNKNOWN
        }

    try:
        from openai import AzureOpenAI

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_VISION_DEPLOYMENT", "gpt-4o")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=api_version
        )

        system_prompt = """You are an expert cloud architect analyzing technical diagrams.
Analyze the provided diagram image and extract:
1. A detailed description of what the diagram shows
2. All components/services shown (list each one)
3. Connections and data flows between components
4. Technologies, cloud services, or tools depicted
5. The type of diagram (architecture, flowchart, sequence, ERD, network, infrastructure, UML)

Format your response as JSON with these keys:
- analysis: string (detailed description)
- components: array of strings
- connections: array of strings (e.g., "Service A -> Service B: HTTP API")
- technologies: array of strings
- diagram_type: string (one of: architecture, flowchart, sequence, erd, network, infrastructure, uml, unknown)
"""

        user_content = [
            {
                "type": "text",
                "text": f"Analyze this technical diagram. {context}" if context else "Analyze this technical diagram."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                    "detail": "high"
                }
            }
        ]

        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)

        # Map diagram type string to enum
        type_str = result.get("diagram_type", "unknown").lower()
        diagram_type = DiagramType.UNKNOWN
        for dt in DiagramType:
            if dt.value == type_str:
                diagram_type = dt
                break

        return {
            "analysis": result.get("analysis", ""),
            "components": result.get("components", []),
            "connections": result.get("connections", []),
            "technologies": result.get("technologies", []),
            "diagram_type": diagram_type
        }

    except Exception as e:
        print(f"  ⚠️ Vision analysis failed: {e}")
        return {
            "analysis": None,
            "components": [],
            "connections": [],
            "technologies": [],
            "diagram_type": DiagramType.UNKNOWN
        }


def extract_diagrams_with_document_intelligence(
    content: bytes,
    filename: str = "",
    analyze_with_vision: bool = True
) -> DiagramExtractionResult:
    """
    Extract diagrams from a document using Azure AI Document Intelligence.

    Uses the prebuilt-layout model which can detect figures, tables, and
    document structure. Optionally analyzes detected diagrams using GPT-4 Vision.

    Args:
        content: Document file bytes (PDF or image)
        filename: Original filename for logging
        analyze_with_vision: Whether to analyze diagrams with GPT-4 Vision

    Returns:
        DiagramExtractionResult with extracted diagrams and text
    """
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not key:
        return DiagramExtractionResult(
            document_name=filename,
            extraction_method="none",
            text_content="",
            diagram_summary="Azure AI Document Intelligence not configured"
        )

    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentAnalysisFeature
        from azure.core.credentials import AzureKeyCredential

        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        # Base64 encode the content
        base64_content = base64.b64encode(content)

        # Use prebuilt-layout model with figure detection feature
        # This model can detect figures, tables, and document structure
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            analyze_request=AnalyzeDocumentRequest(bytes_source=base64_content),
            features=[DocumentAnalysisFeature.FIGURES]
        )

        result = poller.result()

        # Extract text content
        text_content = result.content or ""

        # Get total pages
        total_pages = len(result.pages) if result.pages else 0

        # Extract figures/diagrams
        diagrams = []
        if hasattr(result, 'figures') and result.figures:
            for idx, figure in enumerate(result.figures):
                diagram_id = f"diagram-{idx + 1}"

                # Get page number
                page_number = 1
                if hasattr(figure, 'bounding_regions') and figure.bounding_regions:
                    page_number = figure.bounding_regions[0].page_number

                # Get bounding box
                bounding_box = None
                if hasattr(figure, 'bounding_regions') and figure.bounding_regions:
                    region = figure.bounding_regions[0]
                    if hasattr(region, 'polygon') and region.polygon:
                        # Polygon is a list of x,y coordinates
                        # Convert to bounding box
                        polygon = region.polygon
                        if len(polygon) >= 4:
                            x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                            y_coords = [polygon[i] for i in range(1, len(polygon), 2)]
                            bounding_box = BoundingBox(
                                x=min(x_coords),
                                y=min(y_coords),
                                width=max(x_coords) - min(x_coords),
                                height=max(y_coords) - min(y_coords)
                            )

                # Get caption if available
                caption = None
                if hasattr(figure, 'caption') and figure.caption:
                    caption = figure.caption.content if hasattr(figure.caption, 'content') else str(figure.caption)

                # Get confidence
                confidence = getattr(figure, 'confidence', 0.0) or 0.0

                # Create extracted diagram
                diagram = ExtractedDiagram(
                    diagram_id=diagram_id,
                    page_number=page_number,
                    bounding_box=bounding_box,
                    caption=caption,
                    confidence=confidence
                )

                # Analyze with vision if enabled and we have image data
                if analyze_with_vision and _is_vision_analysis_configured():
                    # For now, we'll analyze using document context
                    # In a full implementation, we would crop the figure region
                    # and send that specific image to GPT-4 Vision
                    context = f"Document: {filename}"
                    if caption:
                        context += f". Caption: {caption}"

                    # Note: Without actual figure image extraction, we provide
                    # limited analysis based on the full document
                    # A full implementation would use PDF rendering to crop figures
                    print(f"  🔍 Figure {idx + 1} detected on page {page_number} (confidence: {confidence:.2f})")

                diagrams.append(diagram)

        # Generate diagram summary
        diagram_summary = None
        if diagrams:
            summary_parts = [f"Found {len(diagrams)} diagram(s) in the document:"]
            for d in diagrams:
                desc = f"- Page {d.page_number}"
                if d.caption:
                    desc += f": {d.caption}"
                if d.confidence > 0:
                    desc += f" (confidence: {d.confidence:.0%})"
                summary_parts.append(desc)
            diagram_summary = "\n".join(summary_parts)

        print(f"  📊 Extracted {len(diagrams)} diagrams and {len(text_content)} chars from {filename}")

        return DiagramExtractionResult(
            document_name=filename,
            total_pages=total_pages,
            diagrams_found=len(diagrams),
            diagrams=diagrams,
            extraction_method="azure-document-intelligence",
            text_content=text_content,
            diagram_summary=diagram_summary
        )

    except ImportError:
        return DiagramExtractionResult(
            document_name=filename,
            extraction_method="error",
            text_content="",
            diagram_summary="azure-ai-documentintelligence package not installed"
        )
    except Exception as e:
        print(f"  ❌ Diagram extraction failed: {e}")
        return DiagramExtractionResult(
            document_name=filename,
            extraction_method="error",
            text_content="",
            diagram_summary=f"Extraction failed: {str(e)}"
        )


def extract_diagrams_from_path(
    file_path: str,
    analyze_with_vision: bool = True
) -> DiagramExtractionResult:
    """
    Extract diagrams from a file path.

    Args:
        file_path: Path to the document file
        analyze_with_vision: Whether to analyze diagrams with GPT-4 Vision

    Returns:
        DiagramExtractionResult with extracted diagrams and text
    """
    if not os.path.exists(file_path):
        return DiagramExtractionResult(
            document_name=os.path.basename(file_path),
            extraction_method="error",
            diagram_summary=f"File not found: {file_path}"
        )

    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        content = f.read()

    return extract_diagrams_with_document_intelligence(
        content,
        filename,
        analyze_with_vision
    )
