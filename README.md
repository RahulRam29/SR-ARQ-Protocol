# SR-ARQ-Protocol
Data transferred across untrustworthy channels risks being lost or corrupted. Preventing data loss is critical for security and IP protection. Some apps cannot work in the event of data loss.

This is addressed by error control mechanisms such as the Selective Repeat Automatic Repeat Request (SR ARQ) Protocol. It works at the Data Link Layer to ensure stable connections and error control.

Sliding Window is used by SR ARQ for sequential data transfer. Both the sender and the receiver keep windows of similar size. As data is sent, the windows shift.

SR ARQ sends suspected/corrupted frames again. Without waiting for all acknowledgments, the sender sends frames. Receivers transmit negative acknowledgements for errors, requesting retransmission. Positive acknowledgements indicate error-free delivery.

