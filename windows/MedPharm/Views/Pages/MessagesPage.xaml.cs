/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MedPharm.Models;

namespace MedPharm.Views.Pages;

public partial class MessagesPage : UserControl
{
    private MessageThread? _selectedThread;

    public MessagesPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await LoadThreads();
    }

    private async Task LoadThreads()
    {
        try
        {
            var resp = await App.Api.GetAsync<MessageThreadsResponse>("patient/messages");
            ThreadsList.ItemsSource = resp.Threads;
            if (_selectedThread == null && resp.Threads.Count > 0)
            {
                ThreadsList.SelectedIndex = 0;
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Messages", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    private async void ThreadsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ThreadsList.SelectedItem is not MessageThread thread) return;
        _selectedThread = thread;
        await LoadThreadDetail(thread.Id);
    }

    private async Task LoadThreadDetail(int threadId)
    {
        try
        {
            var resp = await App.Api.GetAsync<MessageThreadDetailResponse>(
                $"patient/messages/{threadId}");
            ThreadSubject.Text = resp.Thread.Subject;
            ThreadMeta.Text =
                $"With {resp.Thread.ProviderName ?? "your care team"}  ·  Opened {resp.Thread.CreatedAt}";
            MessagesPanel.Children.Clear();
            foreach (var m in resp.Messages)
            {
                MessagesPanel.Children.Add(BuildBubble(m));
            }
            MessagesScroll.ScrollToBottom();

            var isClosed = resp.Thread.IsClosed;
            ClosedNote.Visibility = isClosed ? Visibility.Visible : Visibility.Collapsed;
            ReplyArea.Visibility = isClosed ? Visibility.Collapsed : Visibility.Visible;
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Messages", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    private static UIElement BuildBubble(SecureMessage message)
    {
        var isMe = message.IsFromPatient;

        var border = new Border
        {
            CornerRadius = new CornerRadius(10),
            Padding = new Thickness(10, 8, 10, 8),
            Margin = new Thickness(0, 4, 0, 4),
            MaxWidth = 520,
            HorizontalAlignment = isMe ? HorizontalAlignment.Right : HorizontalAlignment.Left,
            Background = isMe
                ? (Brush)Application.Current.Resources["MPPrimary"]
                : (Brush)Application.Current.Resources["MPSurface"],
        };

        var stack = new StackPanel();

        var labelBrush = isMe
            ? new SolidColorBrush(Color.FromArgb(0xFF, 0x04, 0x12, 0x1A))
            : (Brush)Application.Current.Resources["MPTextMuted"];
        var bodyBrush = isMe
            ? new SolidColorBrush(Color.FromArgb(0xFF, 0x04, 0x12, 0x1A))
            : (Brush)Application.Current.Resources["MPText"];
        var timeBrush = isMe
            ? new SolidColorBrush(Color.FromArgb(0xFF, 0x04, 0x12, 0x1A)) { Opacity = 0.75 }
            : (Brush)Application.Current.Resources["MPTextMuted"];

        stack.Children.Add(new TextBlock
        {
            Text = message.SenderLabel,
            FontSize = 11,
            FontWeight = FontWeights.SemiBold,
            Foreground = labelBrush,
        });
        stack.Children.Add(new TextBlock
        {
            Text = message.Body,
            TextWrapping = TextWrapping.Wrap,
            Foreground = bodyBrush,
            Margin = new Thickness(0, 2, 0, 2),
        });
        stack.Children.Add(new TextBlock
        {
            Text = message.SentAt ?? "",
            FontSize = 10,
            Foreground = timeBrush,
        });

        border.Child = stack;
        return border;
    }

    private async void SendBtn_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedThread == null) return;
        var body = ReplyInput.Text?.Trim() ?? "";
        if (string.IsNullOrEmpty(body)) return;
        SendBtn.IsEnabled = false;
        try
        {
            await App.Api.PostAsync<MessageResponse>(
                $"patient/messages/{_selectedThread.Id}/reply",
                new { body });
            ReplyInput.Clear();
            await LoadThreadDetail(_selectedThread.Id);
            await LoadThreads();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Reply failed", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        finally
        {
            SendBtn.IsEnabled = true;
        }
    }

    private async void NewMessageBtn_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new NewMessageDialog
        {
            Owner = Window.GetWindow(this),
        };
        if (dialog.ShowDialog() == true && dialog.NewThreadId.HasValue)
        {
            await LoadThreads();
            foreach (var item in ThreadsList.Items)
            {
                if (item is MessageThread t && t.Id == dialog.NewThreadId)
                {
                    ThreadsList.SelectedItem = t;
                    break;
                }
            }
        }
    }
}
