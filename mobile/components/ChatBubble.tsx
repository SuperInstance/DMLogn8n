import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import {
  Text,
  Avatar,
  Icon,
  Button,
  Overlay,
} from 'react-native-elements';
import { useTheme } from '@react-navigation/native';
import { ChatMessage } from '../types';
import { formatDistanceToNow } from 'date-fns';

interface ChatBubbleProps {
  message: ChatMessage;
  isOwn: boolean;
  onPress?: (message: ChatMessage) => void;
  onLongPress?: (message: ChatMessage) => void;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  consecutive?: boolean;
}

const { width: screenWidth } = Dimensions.get('window');

const ChatBubble: React.FC<ChatBubbleProps> = ({
  message,
  isOwn,
  onPress,
  onLongPress,
  showAvatar = true,
  showTimestamp = true,
  consecutive = false,
}) => {
  const theme = useTheme();
  const [showActions, setShowActions] = useState(false);
  const scaleValue = React.useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleValue, {
      toValue: 0.98,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleValue, {
      toValue: 1,
      useNativeDriver: true,
    }).start();
  };

  const handlePress = () => {
    onPress?.(message);
  };

  const handleLongPress = () => {
    onLongPress?.(message);
    setShowActions(true);
  };

  const handleReaction = (emoji: string) => {
    // Handle reaction logic
    console.log('Adding reaction:', emoji, 'to message:', message.id);
    setShowActions(false);
  };

  const handleReply = () => {
    // Handle reply logic
    console.log('Replying to message:', message.id);
    setShowActions(false);
  };

  const handleCopy = () => {
    // Handle copy logic
    console.log('Copying message:', message.id);
    setShowActions(false);
  };

  const handleDelete = () => {
    // Handle delete logic
    console.log('Deleting message:', message.id);
    setShowActions(false);
  };

  const getMessageBubbleStyle = () => {
    const baseStyle = [styles.messageBubble];

    if (isOwn) {
      baseStyle.push([
        styles.ownMessage,
        {
          backgroundColor: theme.colors.messageOwn,
          borderTopRightRadius: 4,
        },
      ]);
    } else {
      baseStyle.push([
        styles.otherMessage,
        {
          backgroundColor: theme.colors.messageOther,
          borderTopLeftRadius: 4,
        },
      ]);
    }

    if (consecutive) {
      baseStyle.push(styles.consecutiveMessage);
    }

    return baseStyle;
  };

  const getMessageTextStyle = () => {
    const baseStyle = [styles.messageText];

    if (isOwn) {
      baseStyle.push({ color: '#FFFFFF' });
    } else {
      baseStyle.push({ color: theme.colors.text });
    }

    return baseStyle;
  };

  const renderMessageContent = () => {
    switch (message.type) {
      case 'text':
        return (
          <Text style={getMessageTextStyle()}>
            {message.content}
          </Text>
        );

      case 'image':
        return (
          <View style={styles.imageContainer}>
            {/* Image rendering logic */}
            <Text style={getMessageTextStyle()}>
              📎 Image: {message.content}
            </Text>
          </View>
        );

      case 'audio':
        return (
          <View style={styles.audioContainer}>
            <Icon
              name="musical-notes"
              type="ionicon"
              size={20}
              color={isOwn ? '#FFFFFF' : theme.colors.primary}
            />
            <Text style={[getMessageTextStyle(), styles.audioText]}>
              🎵 Audio Message
            </Text>
          </View>
        );

      case 'dice_roll':
        return (
          <View style={styles.diceContainer}>
            <Icon
              name="dice"
              type="ionicon"
              size={20}
              color={theme.colors.warning}
            />
            <Text style={getMessageTextStyle()}>
              🎲 {message.content}
            </Text>
          </View>
        );

      case 'game_event':
        return (
          <View style={styles.gameEventContainer}>
            <Icon
              name="game-controller"
              type="ionicon"
              size={20}
              color={theme.colors.info}
            />
            <Text style={getMessageTextStyle()}>
              🎮 {message.content}
            </Text>
          </View>
        );

      case 'system':
        return (
          <View style={[styles.systemContainer, { backgroundColor: theme.colors.systemMessage }]}>
            <Icon
              name="information-circle"
              type="ionicon"
              size={16}
              color={theme.colors.textSecondary}
            />
            <Text style={[styles.systemText, { color: theme.colors.textSecondary }]}>
              {message.content}
            </Text>
          </View>
        );

      default:
        return (
          <Text style={getMessageTextStyle()}>
            {message.content}
          </Text>
        );
    }
  };

  const renderReactions = () => {
    if (!message.reactions || message.reactions.length === 0) {
      return null;
    }

    return (
      <View style={styles.reactionsContainer}>
        {message.reactions.map((reaction, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.reactionBubble,
              { backgroundColor: theme.colors.surfaceVariant },
            ]}
            onPress={() => handleReaction(reaction.emoji)}
          >
            <Text style={styles.reactionEmoji}>{reaction.emoji}</Text>
            <Text style={[styles.reactionCount, { color: theme.colors.textSecondary }]}>
              {reaction.count}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderReplyPreview = () => {
    if (!message.replyTo) {
      return null;
    }

    return (
      <View style={[styles.replyPreview, { backgroundColor: theme.colors.surfaceVariant }]}>
        <Icon
          name="return-up-back"
          type="ionicon"
          size={14}
          color={theme.colors.textSecondary}
        />
        <Text style={[styles.replyText, { color: theme.colors.textSecondary }]}>
          Replying to a message
        </Text>
      </View>
    );
  };

  const renderAttachment = () => {
    if (!message.attachments || message.attachments.length === 0) {
      return null;
    }

    return (
      <View style={styles.attachmentsContainer}>
        {message.attachments.map((attachment) => (
          <View
            key={attachment.id}
            style={[
              styles.attachmentBubble,
              { backgroundColor: theme.colors.surfaceVariant },
            ]}
          >
            <Icon
              name={getAttachmentIcon(attachment.type)}
              type="ionicon"
              size={16}
              color={theme.colors.primary}
            />
            <Text
              style={[styles.attachmentName, { color: theme.colors.text }]}
              numberOfLines={1}
            >
              {attachment.name}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  return (
    <View style={[styles.container, isOwn ? styles.ownContainer : styles.otherContainer]}>
      {/* Avatar */}
      {!isOwn && showAvatar && !consecutive && (
        <Avatar
          size="small"
          rounded
          source={
            message.senderAvatar
              ? { uri: message.senderAvatar }
              : undefined
          }
          title={message.senderName.charAt(0)}
          containerStyle={styles.avatar}
        />
      )}

      {/* Message Container */}
      <View style={styles.messageContainer}>
        {/* Sender Name (for group chats) */}
        {!isOwn && !consecutive && (
          <Text style={[styles.senderName, { color: theme.colors.textSecondary }]}>
            {message.senderName}
          </Text>
        )}

        {/* Message Bubble */}
        <Animated.View
          style={[
            getMessageBubbleStyle(),
            {
              transform: [{ scale: scaleValue }],
            },
          ]}
        >
          {/* Reply Preview */}
          {renderReplyPreview()}

          {/* Message Content */}
          <TouchableOpacity
            onPress={handlePress}
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            onLongPress={handleLongPress}
            activeOpacity={0.7}
            style={styles.messageContent}
          >
            {renderMessageContent()}
          </TouchableOpacity>

          {/* Attachments */}
          {renderAttachment()}

          {/* Timestamp */}
          {showTimestamp && (
            <Text
              style={[
                styles.timestamp,
                {
                  color: isOwn ? '#FFFFFF80' : theme.colors.textSecondary,
                  textAlign: isOwn ? 'right' : 'left',
                },
              ]}
            >
              {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
            </Text>
          )}
        </Animated.View>

        {/* Reactions */}
        {renderReactions()}
      </View>

      {/* Actions Overlay */}
      <Overlay
        isVisible={showActions}
        onBackdropPress={() => setShowActions(false)}
        overlayStyle={[
          styles.actionsOverlay,
          { backgroundColor: theme.colors.surface },
        ]}
      >
        <View style={styles.actionsContainer}>
          <Text style={[styles.actionsTitle, { color: theme.colors.text }]}>
            Message Actions
          </Text>

          <View style={styles.actionsList}>
            <Button
              type="clear"
              title="Reply"
              icon={<Icon name="return-up-back" type="ionicon" color={theme.colors.primary} />}
              onPress={handleReply}
              buttonStyle={styles.actionButton}
            />

            <Button
              type="clear"
              title="Copy"
              icon={<Icon name="copy" type="ionicon" color={theme.colors.primary} />}
              onPress={handleCopy}
              buttonStyle={styles.actionButton}
            />

            <View style={styles.reactionsList}>
              <Text style={[styles.reactionsTitle, { color: theme.colors.textSecondary }]}>
                React
              </Text>
              <View style={styles.emojiReactions}>
                {['❤️', '😂', '😮', '😢', '👍', '👎'].map((emoji) => (
                  <TouchableOpacity
                    key={emoji}
                    style={styles.emojiButton}
                    onPress={() => handleReaction(emoji)}
                  >
                    <Text style={styles.emoji}>{emoji}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {isOwn && (
              <Button
                type="clear"
                title="Delete"
                icon={<Icon name="trash" type="ionicon" color={theme.colors.error} />}
                onPress={handleDelete}
                buttonStyle={styles.actionButton}
                titleStyle={{ color: theme.colors.error }}
              />
            )}
          </View>

          <Button
            title="Cancel"
            type="outline"
            onPress={() => setShowActions(false)}
            buttonStyle={styles.cancelButton}
          />
        </View>
      </Overlay>
    </View>
  );
};

const getAttachmentIcon = (type: string): string => {
  switch (type) {
    case 'image': return 'image';
    case 'audio': return 'musical-notes';
    case 'document': return 'document-text';
    case 'character_sheet': return 'person';
    case 'dice_result': return 'dice';
    default: return 'attach';
  }
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    marginVertical: 2,
    maxWidth: screenWidth * 0.75,
  },
  ownContainer: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
  },
  otherContainer: {
    alignSelf: 'flex-start',
  },
  avatar: {
    marginRight: 8,
    marginLeft: 0,
  },
  messageContainer: {
    flex: 1,
  },
  senderName: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
    marginLeft: 12,
  },
  messageBubble: {
    borderRadius: 20,
    padding: 12,
    paddingVertical: 8,
    minWidth: 60,
    maxWidth: '100%',
  },
  ownMessage: {
    borderBottomRightRadius: 4,
    marginLeft: 'auto',
  },
  otherMessage: {
    borderBottomLeftRadius: 4,
    marginRight: 'auto',
  },
  consecutiveMessage: {
    marginTop: 2,
    borderRadius: 16,
  },
  messageContent: {
    // Message content styles
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  imageContainer: {
    alignItems: 'center',
  },
  audioContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  audioText: {
    // Audio text style
  },
  diceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gameEventContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  systemContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 8,
    borderRadius: 12,
    backgroundColor: '#333',
  },
  systemText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  replyPreview: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    padding: 6,
    borderRadius: 8,
    marginBottom: 6,
  },
  replyText: {
    fontSize: 12,
  },
  attachmentsContainer: {
    marginTop: 6,
    gap: 6,
  },
  attachmentBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 8,
    borderRadius: 8,
  },
  attachmentName: {
    fontSize: 14,
    flex: 1,
  },
  timestamp: {
    fontSize: 10,
    marginTop: 4,
    fontStyle: 'italic',
  },
  reactionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 6,
    marginLeft: isOwn ? 'auto' : 0,
    marginRight: isOwn ? 0 : 'auto',
  },
  reactionBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    padding: 4,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: '#333',
  },
  reactionEmoji: {
    fontSize: 14,
  },
  reactionCount: {
    fontSize: 12,
    fontWeight: '600',
  },
  actionsOverlay: {
    borderRadius: 16,
    padding: 0,
    width: screenWidth * 0.9,
    maxWidth: 320,
  },
  actionsContainer: {
    padding: 20,
  },
  actionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
  },
  actionsList: {
    gap: 8,
    marginBottom: 20,
  },
  actionButton: {
    justifyContent: 'flex-start',
    paddingVertical: 12,
  },
  reactionsList: {
    gap: 8,
  },
  reactionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  emojiReactions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 8,
  },
  emojiButton: {
    padding: 8,
  },
  emoji: {
    fontSize: 24,
  },
  cancelButton: {
    marginTop: 10,
  },
});

export default ChatBubble;