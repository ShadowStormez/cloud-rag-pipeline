
import os
from typing import Literal
import logging
from fastapi import HTTPException
from api import app
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.documents import Document
from source_citations import select_cited_sources
import re

load_dotenv()
logger = logging.getLogger(__name__)

# Load expensive components once at application startup
print("Loading database and LLM...")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_unity_test")

db = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embeddings,
)

llm = ChatGroq(model="openai/gpt-oss-20b")

system_prompt = (
    "You are a technical assistant specializing in Unity and Godot "
    "documentation. "
    "Answer using only the retrieved documentation context. "
    "Treat retrieved passages as potential evidence, not proof that "
    "the question is answered. Check that the documentation directly "
    "supports each substantive claim and any code example. "
    "A document mentioning similar words or related APIs is not "
    "sufficient evidence. "
    "If the context is unrelated or does not adequately answer the "
    "question, begin your response with: "
    "'I don't know based on the available documentation.' "
    "Then briefly explain what information is missing, without "
    "guessing or inventing a solution. "
    "Do not invent methods, properties, class names, or APIs. "
    "Do not mix APIs from different game engines or versions. "
    "For Godot questions, use Godot 4 GDScript syntax and APIs. "
    "For GDScript examples, use exactly four spaces per indentation level, "
    "with consistent indentation throughout each code block. "
    "Every function, if, elif, else, and loop must have a correctly "
    "indented executable statement in its body; comments alone do not "
    "count as executable statements. "
    "Before responding, check each code example for indentation errors, "
    "missing block bodies, undefined variables, and incorrect node paths. "
    "If you cannot provide a reliable executable example, explain "
    "the documented API without inventing code. "
    "Never recommend removed Godot 3 classes such as "
    "KinematicBody2D; use CharacterBody2D instead. "
    "Distinguish between editor Inspector properties and "
    "GDScript methods. Only use properties and methods "
    "documented for the specific class being discussed. "
    "Before writing code, verify method arguments, return "
    "values, and built-in properties against the retrieved "
    "API definitions. Never redeclare inherited properties "
    "or pass arguments to parameterless methods. "
    "For Godot Area2D detection, distinguish physics bodies from areas: "
    "use body_entered for CharacterBody2D or other PhysicsBody2D nodes, "
    "and area_entered for another Area2D. Use shape-specific signals "
    "only when individual collision shapes must be identified. "
    "Verify collision shapes, monitoring, and collision layers/masks "
    "against the retrieved documentation. "
    "Use modern signal connections such as "
    "area.body_entered.connect(callback), not deprecated "
    "Godot 3 connection syntax. "
    "If the context does not contain enough information, "
    "explicitly say what is unknown. "
    "Prefer concise, accurate explanations over exhaustive lists. "
    "When an engine is selected, answer specifically for that engine.\n\n"
    "Every code example must use APIs and syntax supported by "
    "the retrieved documentation. Never invent implementation details. "
    "If the documentation does not provide enough information "
    "for a reliable code example, explain the concept instead. "
    "For Unity questions, distinguish editor workflows from "
    "runtime C# APIs. "
    "For Unity physics examples, distinguish Update() from "
    "FixedUpdate(): do not place one-frame input checks such as "
    "Input.GetKeyDown() inside FixedUpdate(). When necessary, "
    "capture input in Update() and apply physics in FixedUpdate(). "
    "Do not claim that every Rigidbody2D body type is affected "
    "by gravity or responds to forces identically. "
    "Keep Rigidbody (3D) and Rigidbody2D (2D) APIs separate, "
    "and verify method availability against the retrieved context. "
    "Verify data-binding direction and do not "
    "assume a binding can be assigned directly to a UI property. "
    "Each retrieved document has a numbered Source identifier. "
    "Only cite documents that directly support your answer. "
    "Do not put citation numbers or source references inside code blocks, "
    "code comments, or inline code. "
    "Do not insert numbered citations throughout the explanation; "
    "the application displays cited documentation separately. "
    "At the very end of your response, add exactly one line in this format: "
    "Sources used: [1], [3] "
    "Use the actual source numbers provided in the context. "
    "Do not cite unrelated documents or invent source numbers. "
    "If no document supports the answer, write: Sources used: none. "
    "Retrieved documentation:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

document_prompt = PromptTemplate.from_template(
    "Source [{source_number}]\n"
    "URL: {source_url}\n"
    "{page_content}"
)

question_answer_chain = create_stuff_documents_chain(
    llm,
    prompt,
    document_prompt=document_prompt,
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    engine: Literal["auto", "unity", "godot"] = "auto"

def find_godot_class_urls(question: str) -> list[str]:
    """Find all explicitly mentioned Godot classes with indexed documentation."""

    class_names = re.findall(
        r"\b[A-Z][A-Za-z0-9]*\b",
        question,
    )

    urls = []

    for class_name in dict.fromkeys(class_names):
        url = (
            "https://docs.godotengine.org/en/stable/"
            f"classes/class_{class_name.lower()}.html"
        )

        matches = db._collection.get(
            where={
                "$and": [
                    {"source_type": "godot"},
                    {"source_url": url},
                ]
            },
            limit=1,
        )

        if matches["ids"] and url not in urls:
            urls.append(url)

    return urls


def expand_neighboring_chunks(documents, max_chunks=15):
    """Expand retrieved documents with adjacent indexed chunks."""
    from langchain_core.documents import Document

    expanded = []
    seen_ids = set()

    for doc in documents:
        source = doc.metadata.get("source")
        source_type = doc.metadata.get("source_type")
        source_url = doc.metadata.get("source_url")

        if not source or not source_type or not source_url:
            expanded.append(doc)
            continue

        records = db._collection.get(
            where={
                "$and": [
                    {"source": source},
                    {"source_type": source_type},
                    {"source_url": source_url},
                ]
            },
            include=["documents", "metadatas"],
        )

        chunks = {
            record_id: (content, metadata)
            for record_id, content, metadata in zip(
                records["ids"],
                records["documents"],
                records["metadatas"],
            )
        }

        matching_ids = [
            record_id
            for record_id, (content, _) in chunks.items()
            if content == doc.page_content
        ]

        if not matching_ids:
            expanded.append(doc)
            continue

        record_id = matching_ids[0]
        prefix, index_text = record_id.rsplit("-", 1)

        if not index_text.isdigit():
            expanded.append(doc)
            continue

        index = int(index_text)

        for neighbor_index in (index, index - 1, index + 1):
            neighbor_id = f"{prefix}-{neighbor_index}"

            if neighbor_id not in chunks:
                continue

            if neighbor_id in seen_ids:
                continue

            content, metadata = chunks[neighbor_id]

            expanded.append(
                Document(
                    page_content=content,
                    metadata=metadata,
                )
            )
            seen_ids.add(neighbor_id)

            if len(expanded) >= max_chunks:
                return expanded

    return expanded[:max_chunks]


def retrieve_with_page_context(engine, question, max_chunks=12):
    """Retrieve relevant passages and neighboring context."""
    from collections import Counter

    # Retrieve both Unity physics APIs for explicit comparisons.
    if (
        engine == "unity"
        and "rigidbody2d" in question.lower()
        and re.search(
            r"\brigidbody\b",
            question,
            flags=re.IGNORECASE,
        )
        and any(
            word in question.lower()
            for word in ("difference", "compare", "versus", " vs ")
        )
    ):
        comparison_docs = []

        for class_name in ("Rigidbody", "Rigidbody2D"):
            url = (
                "https://docs.unity3d.com/6000.0/"
                f"Documentation/ScriptReference/{class_name}.html"
            )

            comparison_docs.extend(
                db.similarity_search(
                    f"Unity {class_name} component physics properties methods",
                    k=5,
                    filter={
                        "$and": [
                            {"source_type": "unity"},
                            {"source_url": url},
                        ]
                    },
                )
            )

        return comparison_docs[:max_chunks]

    # Prioritize explicitly named, indexed Unity API classes.
    unity_class_urls = []
    targeted_docs = []

    if engine == "unity":
        class_names = dict.fromkeys(
            re.findall(r"\b[A-Z][A-Za-z0-9]*\b", question)
        )

        # Keyboard-controlled 2D physics scripts also need
        # input and Unity lifecycle API documentation.
        question_lower = question.lower()
        is_keyboard_controller = (
            "rigidbody2d" in question_lower
            and any(
                term in question_lower
                for term in ("controller", "script")
            )
            and any(
                term in question_lower
                for term in (
                    "keyboard", "input", "space",
                    "jump", "keycode",
                )
            )
        )

        if is_keyboard_controller:
            for supporting_class in (
                "Input",
                "KeyCode",
                "MonoBehaviour",
            ):
                class_names.setdefault(supporting_class, None)

        for class_name in list(class_names)[:12]:
            candidate_urls = (
                (
                    "https://docs.unity3d.com/6000.0/"
                    f"Documentation/ScriptReference/{class_name}.html"
                ),
                (
                    "https://docs.unity.com/en-us/engine/6000.0/"
                    f"script-reference/unityengine/{class_name.lower()}"
                ),
            )

            for url in candidate_urls:
                matches = db._collection.get(
                    where={
                        "$and": [
                            {"source_type": "unity"},
                            {"source_url": url},
                        ]
                    },
                    limit=1,
                )

                if not matches["ids"]:
                    continue

                unity_class_urls.append(url)
                targeted_docs.extend(
                    db.similarity_search(
                        question,
                        k=5,
                        filter={
                            "$and": [
                                {"source_type": "unity"},
                                {"source_url": url},
                            ]
                        },
                    )
                )

                # Avoid retrieving the same class twice when
                # both URL formats are indexed.
                break

    # Preserve regular retrieval for additional context and
    # questions without explicitly named API classes.
    base_retriever = build_retriever(engine, question)
    initial = base_retriever.invoke(question)

    if not initial and not targeted_docs:
        return []

    initial = targeted_docs + list(initial)

    # Identify relevant pages without assuming a single source.
    page_counts = Counter(
        doc.metadata.get("source_url")
        for doc in initial
        if doc.metadata.get("source_url")
    )

    selected_pages = [
        url
        for url, _ in page_counts.most_common(2)
    ]

    candidates = list(initial)

    # Search within the selected pages for implementation context.
    for page_index, page_url in enumerate(selected_pages):
        filters = {"source_url": page_url}

        if engine != "auto":
            filters = {
                "$and": [
                    {"source_type": engine},
                    {"source_url": page_url},
                ]
            }

        # Give the dominant page a deeper implementation search.
        if engine == "unity" and page_index == 0:
            focused_query = question + " C# code example implementation"
            focused_k = 10
        else:
            focused_query = question
            focused_k = 5

        focused = db.similarity_search(
            focused_query,
            k=focused_k,
            filter=filters,
        )

        candidates.extend(focused)

        # Retrieve property declarations and API definitions from
        # the same documentation page, not only descriptive passages.
        if engine == "godot":
            property_docs = db.similarity_search(
                question
                + " property declarations built-in member variables "
                + "velocity Vector2 method signature",
                k=8,
                filter=filters,
            )
            candidates.extend(property_docs)

    # Prefer code-bearing passages without discarding explanations.
    def code_score(doc):
        content = doc.page_content
        indicators = (
            "public ", "using ", "new ", "var ",
            "();", "=>", "{", "}",
            "func ", "extends ", "signal ",
        )
        return sum(
            indicator in content
            for indicator in indicators
        )

    # Prioritize API definitions for methods explicitly named
    # in the question, together with relevant property declarations.
    method_names = set(
        re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", question.lower())
    )

    def api_definition_score(doc):
        content = doc.page_content.lower()
        score = 0

        for method in method_names:
            # Match documented signatures such as:
            # bool move_and_slide ()
            signature = re.search(
                rf"\b(?:bool|void|int|float|vector2|vector3|"
                rf"string|variant|array|dictionary)\s+"
                rf"{re.escape(method)}\s*\(",
                content,
            )
            if signature:
                score += 10

        # Prefer explicit property declarations, particularly
        # when their names appear in the question or relevant
        # retrieved method descriptions.
        if re.search(
            r"\b(?:vector2|vector3|float|int|bool|string)\s+"
            r"[a-z_][a-z0-9_]*\s*=",
            content,
        ):
            score += 3

        return score

    # Prioritize documented Godot signals for area entry/exit questions.
    # This prevents property-heavy API pages from crowding out the
    # signal definitions needed to answer the question.
    question_lower = question.lower()
    is_godot_area_signal_question = (
        engine == "godot"
        and "area2d" in question_lower
        and any(
            term in question_lower
            for term in (
                "enter", "exit", "detect", "overlap", "signal",
            )
        )
    )

    def godot_signal_score(doc):
        if not is_godot_area_signal_question:
            return 0

        content = doc.page_content.lower()
        score = 0

        for signal in ("body_entered", "area_entered"):
            if re.search(
                rf"\b{signal}\s*\(",
                content,
            ):
                score += 10

        return score

    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (
            -int(
                item[1].metadata.get("source_url")
                in unity_class_urls
            ),
            -godot_signal_score(item[1]),
            -api_definition_score(item[1]),
            -code_score(item[1]),
            item[0],
        ),
    )

    unique = []
    seen = set()

    for _, doc in ranked:
        key = (
            doc.metadata.get("source_url"),
            doc.page_content,
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(doc)

    # Give distinct documentation pages an opportunity to contribute
    # context before taking additional chunks from the same page.
    # The first occurrence of each URL retains its ranking priority.
    first_per_page = []
    remaining = []
    seen_pages = set()

    for doc in unique:
        page_url = doc.metadata.get("source_url")

        if page_url and page_url not in seen_pages:
            first_per_page.append(doc)
            seen_pages.add(page_url)
        else:
            remaining.append(doc)

    diverse_candidates = first_per_page + remaining

    return expand_neighboring_chunks(
        diverse_candidates,
        max_chunks=max_chunks,
    )

def build_retriever(engine: str, question: str = ""):
    search_kwargs = {"k": 5}

    if engine != "auto":
        search_kwargs["filter"] = {
            "source_type": engine
        }

    if engine == "godot" and question:
        class_urls = find_godot_class_urls(question)

        if len(class_urls) == 1:
            search_kwargs["filter"] = {
                "source_url": class_urls[0]
            }

        elif len(class_urls) > 1:
            search_kwargs["filter"] = {
                "$and": [
                    {"source_type": "godot"},
                    {
                        "source_url": {
                            "$in": class_urls
                        }
                    },
                ]
            }

    return db.as_retriever(
        search_kwargs=search_kwargs
    )

@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        documents = retrieve_with_page_context(
            request.engine,
            request.question,
            max_chunks=10,
        )

        if not documents:
            return {
                "answer": (
                    "I couldn't find relevant documentation to answer "
                    "that question reliably. Try specifying a Unity or "
                    "Godot component, class, or feature."
                ),
                "sources": [],
            }

        numbered_documents = [
            Document(
                page_content=doc.page_content,
                metadata={
                    **doc.metadata,
                    "source_number": index,
                    "source_url": doc.metadata.get(
                        "source_url", "unknown"
                    ),
                },
            )
            for index, doc in enumerate(documents, start=1)
        ]

        answer = question_answer_chain.invoke({
            "input": request.question,
            "context": numbered_documents,
        })

        if not isinstance(answer, str) or not answer.strip():
            logger.warning("RAG model returned an empty answer")
            return {
                "answer": (
                    "I couldn't generate a reliable answer this time. "
                    "Please try again or rephrase your question."
                ),
                "sources": [],
            }

        # An explicit lack-of-evidence answer must not cite retrieved
        # documents as though they support a factual conclusion.
        normalized_answer = answer.strip().lower()
        unsupported_prefixes = (
            "i don't know",
            "i do not know",
            "i cannot determine",
            "i can't determine",
            "the available documentation does not",
            "there isn't enough information",
            "there is not enough information",
        )

        if normalized_answer.startswith(unsupported_prefixes):
            return {
                "answer": answer,
                "sources": [],
            }

        clean_answer, cited_documents = select_cited_sources(
            answer,
            documents,
        )

        sources = [
            {
                "metadata": doc.metadata,
                "content": doc.page_content,
            }
            for doc in cited_documents
        ]

        return {
            "answer": clean_answer,
            "sources": sources,
        }

    except Exception:
        logger.exception("RAG request failed")

        raise HTTPException(
            status_code=503,
            detail=(
                "The AI assistant is temporarily unavailable. "
                "Please try again later."
            ),
        ) from None
