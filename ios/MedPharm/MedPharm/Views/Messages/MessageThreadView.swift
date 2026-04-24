/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MessageThreadView: View {
    let threadId: Int

    @State private var thread: MessageThread?
    @State private var messages: [SecureMessage] = []
    @State private var replyText: String = ""
    @State private var isSending = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            MPColor.bg.ignoresSafeArea()
            VStack(spacing: 0) {
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(messages) { m in
                                MessageBubble(message: m).id(m.id)
                            }
                        }
                        .padding(12)
                    }
                    .onChange(of: messages.count) {
                        if let last = messages.last {
                            withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                        }
                    }
                }
                if let t = thread, t.is_closed {
                    Text("This thread is closed.")
                        .font(.footnote.italic())
                        .foregroundColor(MPColor.textMuted)
                        .padding()
                } else {
                    Divider().background(MPColor.border)
                    HStack(alignment: .bottom, spacing: 8) {
                        TextField("Type your reply…", text: $replyText, axis: .vertical)
                            .textFieldStyle(.plain)
                            .lineLimit(1...4)
                            .padding(8)
                            .background(MPColor.surface)
                            .cornerRadius(8)
                            .foregroundColor(MPColor.text)
                        Button {
                            Task { await send() }
                        } label: {
                            Image(systemName: "paperplane.fill")
                                .foregroundColor(.white)
                                .padding(10)
                                .background(MPColor.primary)
                                .clipShape(Circle())
                        }
                        .disabled(replyText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
                    }
                    .padding(8)
                    .background(MPColor.bgElevated)
                }
            }
        }
        .navigationTitle(thread?.subject ?? "Conversation")
        .navigationBarTitleDisplayMode(.inline)
        .alert("Error", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task { await load() }
    }

    private func load() async {
        do {
            let detail: MessageThreadDetail = try await APIClient.shared
                .request("patient/messages/\(threadId)")
            thread = detail.thread
            messages = detail.messages
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func send() async {
        let text = replyText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        isSending = true
        defer { isSending = false }
        do {
            let _: MessageResponse = try await APIClient.shared.request(
                "patient/messages/\(threadId)/reply",
                method: "POST",
                body: ReplyRequest(body: text))
            replyText = ""
            await load()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct MessageBubble: View {
    let message: SecureMessage

    var isMe: Bool { message.sender_type == "patient" }

    var body: some View {
        HStack {
            if isMe { Spacer(minLength: 40) }
            VStack(alignment: isMe ? .trailing : .leading, spacing: 2) {
                Text(message.body)
                    .foregroundColor(isMe ? .white : MPColor.text)
                    .padding(10)
                    .background(isMe ? MPColor.primary : MPColor.surface)
                    .cornerRadius(12)
                    .frame(maxWidth: 280, alignment: isMe ? .trailing : .leading)
                Text(message.sent_at ?? "")
                    .font(.caption2)
                    .foregroundColor(MPColor.textMuted)
            }
            if !isMe { Spacer(minLength: 40) }
        }
    }
}
