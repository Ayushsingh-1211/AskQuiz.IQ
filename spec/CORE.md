# CORE - product, chunks, spoiler rule

## Product
Watch, pause, ask. Answers use only what the learner has already seen/heard (speech, screen, permitted docs), carry verifiable citations, refuse when unsupported. Same data powers an adaptive mock interview. Ingest once, answer many times.

## Chunks (every source type)
`chunks(id uuid pk, video_id uuid, doc_id uuid, source_type text [speech|screen|pdf|ppt|notes|code], text, start_s real, end_s real, visible_from_s real, page int, slide int, frame_path text, meta jsonb, embedding vector(384), tsv tsvector generated from to_tsvector('simple', text))`. Indexes: hnsw(embedding vector_cosine_ops), gin(tsv), btree(video_id, visible_from_s). Other tables: users, videos, jobs(stage,status,error,attempts), documents, chat_sessions, messages(pause_t stored), interviews, interview_turns, eval_runs.

## visible_from_s (the spoiler rule)
speech chunk (15-20 s) = end_s | screen frame = frame timestamp | doc page/slide in aligned mode = first time the video clearly covers it | doc in permitted mode = 0. Search: `WHERE video_id=$1 AND visible_from_s <= $pause_t`.

