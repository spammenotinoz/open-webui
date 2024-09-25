<script lang="ts">
  import { toast } from 'svelte-sonner';
  import dayjs from 'dayjs';

  import { createEventDispatcher } from 'svelte';
  import { onMount, tick, getContext } from 'svelte';

  const i18n = getContext<Writable<i18nType>>('i18n');

  const dispatch = createEventDispatcher();

  import { config, models, settings, user } from '$lib/stores';
  import { synthesizeOpenAISpeech } from '$lib/apis/audio';
  import { imageGenerations } from '$lib/apis/images';
  import {
    copyToClipboard as _copyToClipboard,
    approximateToHumanReadable,
    extractParagraphsForAudio,
    extractSentencesForAudio,
    cleanText,
    getMessageContentParts
  } from '$lib/utils';
  import { WEBUI_BASE_URL } from '$lib/constants';

  import Name from './Name.svelte';
  import ProfileImage from './ProfileImage.svelte';
  import Skeleton from './Skeleton.svelte';
  import Image from '$lib/components/common/Image.svelte';
  import Tooltip from '$lib/components/common/Tooltip.svelte';
  import RateComment from './RateComment.svelte';
  import Spinner from '$lib/components/common/Spinner.svelte';
  import WebSearchResults from './ResponseMessage/WebSearchResults.svelte';
  import Sparkles from '$lib/components/icons/Sparkles.svelte';
  import Markdown from './Markdown.svelte';
  import Error from './Error.svelte';
  import Citations from './Citations.svelte';

  import type { Writable } from 'svelte/store';
  import type { i18n as i18nType } from 'i18next';

  interface MessageType {
    // ... (message type definition)
  }

  export let history;
  export let messageId;

  let message: MessageType = JSON.parse(JSON.stringify(history.messages[messageId]));
  $: if (history.messages) {
    if (JSON.stringify(message) !== JSON.stringify(history.messages[messageId])) {
      message = JSON.parse(JSON.stringify(history.messages[messageId]));
    }
  }

  export let siblings;

  export let showPreviousMessage: Function;
  export let showNextMessage: Function;

  export let editMessage: Function;
  export let rateMessage: Function;

  export let continueResponse: Function;
  export let regenerateResponse: Function;

  export let isLastMessage = true;
  export let readOnly = false;

  let model = null;
  $: model = $models.find((m) => m.id === message.model);

  let edit = false;
  let editedContent = '';
  let editTextAreaElement: HTMLTextAreaElement;

  let audioParts: Record<number, HTMLAudioElement | null> = {};
  let speaking = false;
  let speakingIdx: number | undefined;

  let loadingSpeech = false;
  let generatingImage = false;

  let showRateComment = false;

  const copyToClipboard = async (text) => {
    const res = await _copyToClipboard(text);
    if (res) {
      toast.success($i18n.t('Copying to clipboard was successful!'));
    }
  };

  // ... (other function definitions)

  const generateImage = async (message: MessageType) => {
    generatingImage = true;
    try {
      const res = await imageGenerations(localStorage.token, message.content);
      if (res) {
        const files = res.map((image) => ({
          type: 'image',
          url: `${image.url}`
        }));
        dispatch('save', { ...message, files: files });
      }
    } catch (error) {
      toast.error(error);
    } finally {
      generatingImage = false;
    }
  };

  $: if (!edit) {
    (async () => {
      await tick();
    })();
  }

  onMount(async () => {
    console.log('ResponseMessage mounted');
    await tick();
  });
</script>

{#key message.id}
  <div
    class=" flex w-full message-{message.id}"
    id="message-{message.id}"
    dir={$settings.chatDirection}
  >
    <ProfileImage
      src={model?.info?.meta?.profile_image_url ??
        ($i18n.language === 'dg-DG' ? `/doge.png` : `${WEBUI_BASE_URL}/static/favicon.png`)}
    />

    <div class="w-full overflow-hidden pl-1">
      <Name>
        {model?.name ?? message.model}

        {#if message.timestamp}
          <span
            class=" self-center invisible group-hover:visible text-gray-400 text-xs font-medium uppercase ml-0.5 -mt-0.5"
          >
            {dayjs(message.timestamp * 1000).format($i18n.t('h:mm a'))}
          </span>
        {/if}
      </Name>

      <div>
        {#if message?.files && message.files?.filter((f) => f.type === 'image').length > 0}
          <div class="my-2.5 w-full flex overflow-x-auto gap-2 flex-wrap">
            {#each message.files as file}
              <div>
                {#if file.type === 'image'}
                  <Image src={file.url} alt={message.content} />
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        <div class="chat-{message.role} w-full min-w-full markdown-prose">
          {#if (message?.statusHistory ?? [...(message?.status ? [message?.status] : [])]).length > 0}
            {/* ... (status handling code) */}
          {/if}

          {#if edit === true}
            {/* ... (edit mode code) */}
          {:else}
            <div class="w-full flex flex-col">
              {#if message.content === '' && !message.error}
                <Skeleton />
              {:else if message.content && message.error !== true}
                <Markdown id={message.id} content={message.content} {model} />
              {/if}

              {#if message.error}
                <Error content={message?.error?.content ?? message.content} />
              {/if}

              {#if message.citations}
                <Citations citations={message.citations} />
              {/if}
            </div>
          {/if}
        </div>

        {#if !edit}
          {#if message.done || siblings.length > 1}
            <div
              class=" flex justify-start overflow-x-auto buttons text-gray-600 dark:text-gray-500 mt-0.5"
            >
              {/* ... (buttons code) */}
            </div>
          {/if}

          {#if message.done && showRateComment}
            <RateComment
              bind:message
              bind:show={showRateComment}
              on:submit={(e) => {
                dispatch('save', {
                  ...message,
                  annotation: {
                    ...message.annotation,
                    comment: e.detail.comment,
                    reason: e.detail.reason
                  }
                });
                // ... (action dispatch code)
              }}
            />
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/key}

<style>
  /* ... (styles) */
</style>