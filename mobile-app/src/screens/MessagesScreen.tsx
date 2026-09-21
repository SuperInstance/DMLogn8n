import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { fetchCampaignMessages } from '../../store/slices/messageSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const MessagesScreen: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();

  const { campaignMessages, isLoading } = useSelector((state: RootState) => state.messages);

  const [message, setMessage] = React.useState('');

  const handleSendMessage = () => {
    if (message.trim()) {
      // Send message logic
      console.log('Send message:', message);
      setMessage('');
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Messages
        </Text>
      </View>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          <ScrollView contentContainerStyle={styles.content}>
            <View style={[styles.messageContainer, { backgroundColor: theme.colors.surface }]}>
              <Text style={[styles.noMessagesText, { color: theme.colors.textSecondary }]}>
                No messages yet. Start a conversation!
              </Text>
            </View>
          </ScrollView>

          <View style={[styles.inputContainer, { backgroundColor: theme.colors.surface }]}>
            <TextInput
              style={[
                styles.textInput,
                {
                  backgroundColor: theme.colors.background,
                  color: theme.colors.text,
                  borderColor: theme.colors.border,
                },
              ]}
              value={message}
              onChangeText={setMessage}
              placeholder="Type a message..."
              placeholderTextColor={theme.colors.textSecondary}
              multiline
            />
            <TouchableOpacity
              style={[styles.sendButton, { backgroundColor: theme.colors.primary }]}
              onPress={handleSendMessage}
              disabled={!message.trim()}
            >
              <Icon name="send" size={20} color="white" />
            </TouchableOpacity>
          </View>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  messageContainer: {
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  noMessagesText: {
    fontSize: 16,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    maxHeight: 100,
    marginRight: 12,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default MessagesScreen;