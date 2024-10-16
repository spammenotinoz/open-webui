<script lang="ts">
    import { toast } from 'svelte-sonner';
    import { onMount, tick, createEventDispatcher } from 'svelte';
    import { v4 as uuidv4 } from 'uuid'; // Importing UUID library
    import Headphone from './Headphone.svelte'; // Ensure you have this component
    import type { Model } from './types'; // Adjust the import based on your project structure

    // Event Dispatcher
    const dispatch = createEventDispatcher();

    // Props and Exports
    export let autoScroll = false;

    export let atSelectedModel: Model | undefined;
    export let selectedModels: string[] = [''];

    export let history: {
        messages: { [id: string]: Message };
        currentId: string | null;
    } = {
        messages: {},
        currentId: null,
    };

    export let prompt = '';
    export let files: File[] = [];
    export let availableToolIds: string[] = [];
    export let selectedToolIds: string[] = [];
    export let webSearchEnabled = false;

    // References to DOM elements
    let chatTextAreaElement: HTMLTextAreaElement;
    let filesInputElement: HTMLInputElement;

    // State Variables
    let recording = false;
    let dragged = false;
    let user = null;
    export let placeholder = 'Type your message here...';

    // Filtering Vision Capable Models
    let visionCapableModels: Model[] = [];
    $: visionCapableModels = [...(atSelectedModel ? [atSelectedModel] : selectedModels)].filter(
        (modelId) => {
            const model = $models.find((m) => m.id === modelId);
            return model?.info?.meta?.capabilities?.vision ?? true;
        }
    );

    // Auto-resize TextArea
    $: if (prompt) {
        if (chatTextAreaElement) {
            chatTextAreaElement.style.height = '';
            chatTextAreaElement.style.height = Math.min(chatTextAreaElement.scrollHeight, 200) + 'px';
        }
    }

    // Scroll to Bottom Function
    const scrollToBottom = () => {
        const element = document.getElementById('messages-container');
        if (element) {
            element.scrollTo({
                top: element.scrollHeight,
                behavior: 'smooth'
            });
        }
    };

    // Message Interface
    interface Message {
        id: string;
        content: string;
        sender: 'user' | 'response' | 'system';
        timestamp: Date;
        // Add other properties if needed (e.g., attachments, status)
    }

    // onMount Lifecycle Hook
    onMount(() => {
        // Initial Focus
        window.setTimeout(() => {
            chatTextAreaElement?.focus();
        }, 0);

        // Implement Drag and Drop if necessary
        // Example:
        /*
        window.addEventListener('dragover', handleDragOver);
        window.addEventListener('drop', handleDrop);
        return () => {
            window.removeEventListener('dragover', handleDragOver);
            window.removeEventListener('drop', handleDrop);
        };
        */
    });

    // **Instruction Text**
    const instructionText = "Please provide concise responses to all questions or prompts. Aim for clarity and brevity, keeping answers under 40 words.";

    // **Function: Generate Unique ID**
    function generateUniqueId(): string {
        return uuidv4();
    }

    // **Function: Create Message Pair**
    async function createMessagePair(content: string, type: 'user' | 'response' | 'system') {
        try {
            const messageId = generateUniqueId();
            console.log(`Creating ${type} message: ID=${messageId}, Content="${content}"`);

            const newMessage: Message = {
                id: messageId,
                content: content,
                sender: type,
                timestamp: new Date(),
            };

            // Update History Messages
            history.messages = {
                ...history.messages,
                [messageId]: newMessage
            };

            // Update Current ID
            history.currentId = messageId;

            console.log('Current History Messages:', history.messages);

            // Trigger Response Generation for User Messages
            if (type === 'user') {
                await generateResponse(messageId, content);
            }

        } catch (error) {
            console.error(`Error creating ${type} message:`, error);
            toast.error('An error occurred while sending your message.');
        }
    }

    // **Function: Create System Message**
    async function createSystemMessage(content: string) {
        await createMessagePair(content, 'system');
    }

    // **Function: Create User Message**
    async function createUserMessage(content: string) {
        await createMessagePair(content, 'user');
    }

    // **Function: Create Response Message**
    async function createResponseMessage(content: string) {
        await createMessagePair(content, 'response');
    }

    // **Function: Generate Response**
    async function generateResponse(userMessageId: string, userContent: string) {
        console.log(`Generating response for message ID=${userMessageId}, Content="${userContent}"`);
        const responseText = await fetchResponseFromAPI(userContent);
        console.log(`Received response: "${responseText}"`);

        if (responseText && typeof responseText === 'string') {
            await createResponseMessage(responseText);
        } else {
            await createResponseMessage('Sorry, I couldn\'t process that.');
        }
    }

    // **Function: Fetch Response From API**
    async function fetchResponseFromAPI(prompt: string): Promise<string> {
        try {
            const response = await fetch(`${WEBUI_API_BASE_URL}/generate-response`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.token}`, // Ensure token is set
                },
                body: JSON.stringify({ prompt }),
            });

            const data = await response.json();

            if (response.ok && data.responseText) {
                return data.responseText;
            } else {
                console.error('API Error:', data.error || 'Unknown error');
                return 'Sorry, something went wrong.';
            }

        } catch (error) {
            console.error('Fetch Error:', error);
            return 'Sorry, unable to reach the server.';
        }
    }

    // **Handle Call Button Click**
    async function handleCallButtonClick() {
        // Convert messages to an array
        const messagesArray = history.messages ? Object.values(history.messages) : [];
        const firstMessageContent = messagesArray.length > 0 ? messagesArray[0]?.content : null;

        if (!firstMessageContent || !firstMessageContent.includes(instructionText)) {
            // Add the instruction as a system message
            await createSystemMessage(instructionText);
        }

        // Proceed with initiating the call (Implement showCallOverlay and showControls as needed)
        showCallOverlay.set(true);
        showControls.set(true);
    }

    // Placeholder Implementations for showCallOverlay and showControls
    // Replace these with your actual implementations
    import { writable } from 'svelte/store';
    const showCallOverlay = writable(false);
    const showControls = writable(false);

    // **Handle Form Submission (Sending User Message)**
    async function handleSubmit(event: Event) {
        event.preventDefault();
        const userInput = prompt.trim();
        if (userInput) {
            await createUserMessage(userInput);
            prompt = '';
            // Optionally, scroll to bottom after message is added
            await tick();
            scrollToBottom();
        }
    }
</script>

<!-- **Markup/HTML Structure** -->
<div class="chat-container flex flex-col h-full">
    <!-- Messages Display Area -->
    <div id="messages-container" class="flex-1 overflow-y-auto p-4">
        {#each Object.values(history.messages) as message (message.id)}
            {#if message.sender === 'system'}
                <div class="message system-message">
                    {message.content}
                </div>
            {:else if message.sender === 'user'}
                <div class="message user-message">
                    {message.content}
                </div>
            {:else if message.sender === 'response'}
                <div class="message response-message">
                    {message.content}
                </div>
            {/if}
        {/each}
    </div>

    <!-- Input Area -->
    <form on:submit|preventDefault={handleSubmit} class="p-4 border-t">
        <textarea
            bind:value={prompt}
            bind:this={chatTextAreaElement}
            placeholder={placeholder}
            class="w-full p-2 border rounded resize-none"
            rows="1"
            maxLength="1000"
        ></textarea>
        <button type="submit" class="hidden">Send</button>
    </form>

    <!-- Call Button -->
    <button
        class="text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-850 transition rounded-full p-2 self-center m-4"
        type="button"
        on:click={handleCallButtonClick}
        aria-label="Call"
    >
        <Headphone class="size-6" />
    </button>
</div>

<!-- **Styles** -->
<style>
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    #messages-container {
        /* Ensure messages container takes available space and scrolls */
        overflow-y: auto;
    }

    .message {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 8px;
        max-width: 80%;
        word-wrap: break-word;
    }

    .system-message {
        background-color: #f0f0f0;
        font-style: italic;
        color: #555;
        align-self: center;
    }

    .user-message {
        background-color: #dcf8c6;
        align-self: flex-end;
    }

    .response-message {
        background-color: #ffffff;
        align-self: flex-start;
        border: 1px solid #e0e0e0;
    }

    /* Additional styling for responsiveness and aesthetics */
    textarea {
        font-family: inherit;
        font-size: 1rem;
        line-height: 1.5;
    }

    button {
        cursor: pointer;
    }

    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        .system-message {
            background-color: #3a3a3a;
            color: #ccc;
        }

        .user-message {
            background-color: #2f6f44;
            color: #fff;
        }

        .response-message {
            background-color: #424242;
            color: #fff;
            border: 1px solid #555;
        }
    }
</style>