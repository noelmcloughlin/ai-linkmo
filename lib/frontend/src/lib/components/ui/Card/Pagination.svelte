<script lang="ts">
    let {
        currentPage = 0,
        totalPages = 1,
        onPrev,
        onNext
    } = $props();
</script>

<div class="flex items-center gap-2">
    <button
        class="btn btn-xs btn-outline btn-info rounded-lg px-2 py-1"
        onclick={() => { onPrev(); }}
        disabled={false}>&larr; Prev
    </button>
    <span id="pagination-info" class="pagination-info" >
        {currentPage + 1} / {totalPages}
    </span>
    <button
        class="btn btn-xs btn-outline btn-info rounded-lg px-2 py-1"
        onclick={() => { onNext(); }}
        disabled={false}>Next &rarr;
    </button>
</div>

<style>
    /* Custom style for pagination indicator */
    span.pagination-info {
        font-size: 0.81rem;
        font-weight: bold;
        color: #ffffff;
        background-color: #7ea3f3;
        padding: 0.3rem 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        text-align: center;
        display: inline-block;
    }
</style>