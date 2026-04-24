/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MessagesView: View {
    @State private var threads: [MessageThread] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showCompose = false

    var body: some View {
        NavigationStack {
            ZStack {
                MPColor.bg.ignoresSafeArea()
                Group {
                    if isLoading && threads.isEmpty {
                        ProgressView().tint(MPColor.primary)
                    } else if threads.isEmpty {
                        VStack(spacing: 12) {
                            Image(systemName: "bubble.left.and.bubble.right")
                                .font(.system(size: 48))
                                .foregroundColor(MPColor.textMuted)
                            Text("No messages yet")
                                .font(.headline)
                                .foregroundColor(MPColor.text)
                            Text("Start a conversation with your care team.")
                                .font(.subheadline)
                                .foregroundColor(MPColor.textMuted)
                                .multilineTextAlignment(.center)
                            Button { showCompose = true } label: {
                                Label("Compose Message", systemImage: "square.and.pencil")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(MPColor.primary)
                        }
                        .padding(40)
                    } else {
                        List(threads) { thread in
                            NavigationLink(value: thread) {
                                ThreadRow(thread: thread)
                            }
                            .listRowBackground(MPColor.surface)
                        }
                        .scrollContentBackground(.hidden)
                        .refreshable { await load() }
                    }
                }
            }
            .navigationTitle("Messages")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showCompose = true } label: {
                        Image(systemName: "square.and.pencil")
                    }
                }
            }
            .navigationDestination(for: MessageThread.self) { thread in
                MessageThreadView(threadId: thread.id)
            }
            .sheet(isPresented: $showCompose, onDismiss: {
                Task { await load() }
            }) {
                ComposeMessageView()
            }
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
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response: MessageThreadsResponse = try await APIClient.shared
                .request("patient/messages")
            threads = response.threads
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct ThreadRow: View {
    let thread: MessageThread

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
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
                Text("With \(thread.provider_name ?? "your care team")")
                    .font(.caption)
                    .foregroundColor(MPColor.textMuted)
                Text(thread.last_message_at ?? "")
                    .font(.caption2)
                    .foregroundColor(MPColor.textMuted)
            }
        }
        .padding(.vertical, 4)
    }
}
