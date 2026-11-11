# Background reading (source discovery, not prewritten report content)

Read and cite the sources yourself when preparing the original final report.

1. **Jim Gettys and Kathleen Nichols (2011), "Bufferbloat: Dark Buffers in the Internet," ACM Queue.** Foundational discussion of excess buffering and persistent delay. https://queue.acm.org/detail.cfm?id=2071893
2. **IETF RFC 7567 (2015), "IETF Recommendations Regarding Active Queue Management."** Background on avoiding long standing queues and understanding AQM; this project's simulator uses DropTail and does **not** implement AQM. https://www.rfc-editor.org/rfc/rfc7567.html
3. **IETF RFC 8290 (2018), "The Flow Queue CoDel Packet Scheduler and Active Queue Management Algorithm."** Related work for mitigating bufferbloat using queue scheduling/AQM. It is **not** a method directly evaluated here. https://www.rfc-editor.org/rfc/rfc8290.html

Distinguish what each source states from what your generated CSVs independently demonstrate. Do not imply the experiment is a quantitative reproduction of those papers: network and transport models differ.
