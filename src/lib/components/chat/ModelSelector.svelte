<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { setDefaultModels } from '$lib/apis/configs';
    import { models, showSettings, settings, user } from '$lib/stores';
    import { onMount, tick, getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import Selector from './ModelSelector/Selector.svelte';
    import Tooltip from '../common/Tooltip.svelte';

    const i18n = getContext('i18n');

    export let selectedModels = [''];
    export let disabled = false;
    export let showSetDefault = true;

    const dispatch = createEventDispatcher();

    // Add an event handler to trigger the parent's model select function
    const handleModelSelect = () => {
        dispatch('modelSelect');
    };

    const saveDefaultModel = async () => {
        // Function implementation remains the same
    };

    // Map selected models to available models
    $: if (selectedModels.length > 0 && $models.length > 0) {
        selectedModels = selectedModels.map((model) =>
            $models.map((m) => m.id).includes(model) ? model : ''
        );
    }
</script>

<div class="flex flex-col mt-0.5 w-full">
    {#each selectedModels as selectedModel, selectedModelIdx}
        <div class="flex w-full max-w-fit">
            <div class="overflow-hidden w-full">
                <div class="mr-1 max-w-full">
                    <Selector
                        placeholder={$i18n.t('Select a model')}
                        items={$models
                            .filter((model) => model.name !== 'hr')
                            .map((model) => ({
                                value: model.id,
                                label: model.name,
                                info: model
                            }))}
                        bind:value={selectedModel}
                        on:change={handleModelSelect} // Trigger the event when a model is selected
                    />
                </div>
            </div>
        </div>
    {/each}
</div>
