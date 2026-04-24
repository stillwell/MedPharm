/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MessagesView: View {
    @State private var threads: [MessageThread] = []
    @State private var selectedThread: MessageThread?
    @State private var detail: MessageThreadDetail?
    @State private var replyText: String = ""
    @State private var isLoading = false
    @State private var isSending = false
    @State private var errorMessage: String?
    @State private var showCompose = false

    var body: some View {
        HSplitView {
            threadSidebar
                .frame(minWidth: 280, idealWidth: 320, maxWidth: 420)
            conversationPane
                .frame(minWidth: 400)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button { showCompose = true } label: {
                    Label("New Message", systemImage: "square.and.pencil")
                }
            }
            ToolbarItem(placement: .automatic) {
                Button { Task { await loadThreads() } } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
            }
        }
        .sheet(isPresented: $showCompose, onDismiss: {
            Task { await loadThreads() }
        }) {
            ComposeMessageView()
                .frame(width: 520, height: 480)
        }
        .alert("Error", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task { await loadThreads() }
    }

    private var threadSidebar: some View {
        ZStack {
            MPColor.bgElevated.ignoresSafeArea()
            VStack(spacing: 0) {
                HStack {
                    Text("Secure Messages")
                        .font(.headline)
                        .foregroundColor(MPColor.text)
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                Divider().overlay(MPColor.border)
                if isLoading && threads.isEmpty {
                    Spacer()
                    ProgressView().tint(MPColor.primary)
                    Spacer()
                } else if threads.isEmpty {
                    Spacer()
                    VStack(spacing: 8) {
                        Image(systemName: "bubble.left.and.bubble.right")
                            .font(.system(size: 36))
                            .foregroundColor(MPColor.textMuted)
                        Text("No messages yet")
                            .foregroundColor(MPColor.textMuted)
                    }
                    Spacer()
                } else {
                    List(threads, selection: $selectedThread) { thread in
                        ThreadRow(thread: thread)
                            .tag(thread)
                    }
                    .scrollContentBackground(.hidden)
                    .listStyle(.sidebar)
                }
            }
        }
        .onChange(of: selectedThread) {
            guard let t = selectedThread else { return }
            Task { await loadThread(t.id) }
        }
    }

    @ViewBuilder
    private var conversationPane: some View {
        ZStack {
            MPColor.bg.ignoresSafeArea()
            if let detail = detail {
                VStack(spacing: 0) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(detail.thread.subject)
                            .font(.title3.bold())
                            .foregroundColor(MPColor.text)
                        Text("With \(detail.thread.provider_name ?? "your care team")")
                            .font(.subheadline)
                            .foregroundColor(MPColor.textMuted)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(16)
                    Divider().overlay(MPColor.border)
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(spacing: 8) {
                                ForEach(detail.messages) { m in
                                    MessageBubble(message: m).id(m.id)
                                }
                            }
                            .padding(16)
                        }
                        .onChange(of: detail.messages.count) {
                            if let last = detail.messages.last {
                                withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                            }
                        }
                    }
                    if detail.thread.is_closed {
                        Text("This thread is closed.")
                            .font(.footnote.italic())
                            .foregroundColor(MPColor.textMuted)
                            .padding()
                    } else {
                        Divider().overlay(MPColor.border)
                        HStack(alignment: .bottom, spacing: 8) {
                            TextEditor(text: $replyText)
                                .font(.body)
                                .frame(minHeight: 44, maxHeight: 120)
                                .scrollContentBackground(.hidden)
                                .padding(6)
                                .background(MPColor.surface)
                                .cornerRadius(8)
                                .foregroundColor(MPColor.text)
                            Button {
                                Task { await sendReply() }
                            } label: {
                                Label("Send", systemImage: "paperplane.fill")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(MPColor.primary)
                            .disabled(replyText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
                        }
                        .padding(12)
                    }
                }
            } else {
                VStack(spacing: 10) {
                    Image(systemName: "text.bubble")
                        .font(.system(size: 42))
                        .foregroundColor(MPColor.textMuted)
                    Text("Select a conversation")
                        .foregroundColor(MPColor.textMuted)
                }
            }
        }
    }

    private func loadThreads() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: MessageThreadsResponse = try await APIClient.shared
                .request("patient/messages")
            threads = response.threads
            if selectedThread == nil, let first = response.threads.first {
                selectedThread = first
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func loadThread(_ id: Int) async {
        do {
            let response: MessageThreadDetail = try await APIClient.shared
                .request("patient/messages/\(id)")
            detail = response
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func sendReply() async {
        guard let thread = detail?.thread else { return }
        let text = replyText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        isSending = true
        defer { isSending = false }
        do {
            let _: MessageResponse = try await APIClient.shared.request(
                "patient/messages/\(thread.id)/reply",
                method: "POST",
                body: ReplyRequest(body: text))
            replyText = ""
            await loadThread(thread.id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct ThreadRow: View {
    let thread: MessageThread

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(thread.subject)
                    .font(.headline)
                    .foregroundColor(MPColor.text)
                    .lineLimit(1)
                if thread.unread_count > 0 {
                    Text("\(thread.unread_count)")
                        .font(.caption2.bold())
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.red)
                        .clipShape(Capsule())
                }
                if thread.is_closed {
                    Text("Closed")
                        .font(.caption2.italic())
                        .foregroundColor(MPColor.textMuted)
                }
            }
            Text(thread.provider_name ?? "Care team")
                .font(.caption)
                .foregroundColor(MPColor.textMuted)
            Text(thread.last_message_at ?? "")
                .font(.caption2)
                .foregroundColor(MPColor.textMuted)
        }
        .padding(.vertical, 4)
    }
}

struct MessageBubble: View {
    let message: SecureMessage

    var isMe: Bool { message.sender_type == "patient" }

    var body: some View {
        HStack {
            if isMe { Spacer(minLength: 60) }
            VStack(alignment: isMe ? .trailing : .leading, spacing: 2) {
                Text(message.body)
                    .foregroundColor(isMe ? .white : MPColor.text)
                    .padding(10)
                    .background(isMe ? MPColor.primary : MPColor.surface)
                    .cornerRadius(12)
                    .frame(maxWidth: 420, alignment: isMe ? .trailing : .leading)
                Text(message.sent_at ?? "")
                    .font(.caption2)
                    .foregroundColor(MPColor.textMuted)
            }
            if !isMe { Spacer(minLength: 60) }
        }
    }
}
