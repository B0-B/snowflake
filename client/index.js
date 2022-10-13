var app = new Vue({

    el: '#app',
    data: {
        title: "snowflake",
    },
    mounted: async function () {
        document.title = this.title;
    },
    methods: {
       // 
    }
})