//import Supervisor , Worker from "./static/build/plugins/sigma.layout.forceAtlas2.min.js";

document.addEventListener('DOMContentLoaded', () => {

    // Liga o websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);


    // Cria o grafo
    var graph = {
        nodes: [],
        edges: []
    };

    // Inicia o sigma
    var s = new sigma(
    {
        graph: graph,
        renderers: [{
            container: document.getElementById('sigma-container'),
            type: 'canvas'
        }],
        settings: {
            minEdgeSize: 0.1,
            maxEdgeSize: 2,
            minNodeSize: 1,
            maxNodeSize: 8,
            minArrowSize: 10
        }
    });


    // Pede pelos dados
    socket.emit('get_nodes');
    socket.emit('get_edges');


    // Ao receber os dados
    socket.on('get_nodes', data =>
    {
        let x = 0;
        let y = 0;

        for (let point of data)
        {
            //node = {id: point[0], label: point[1], color: "#000000"}
            //graph["nodes"].push(node)
            //console.log(node)
            //console.log(point)

            node = {id: point[0], label: point[1], x: Math.random(), y: Math.random(), size: 3, color: '#000000' }

            //console.log(node)
            //console.log("===========")

            //graph["nodes"].push(node)
            s.graph.addNode(node)
            x++
            y++
        }

    });


    // Ao receber os dados
    socket.on('get_edges', data =>
    {
        let counter = 0;

        for (let point of data)
        {

            edge = {
                id: counter,
                source: point[0],
                target: point[1],
                color: "#000000",
                size:1,
                type:'arrow',
             }

            //console.log(edge)
            //graph["edges"].push(edge)
            //graph.edges.push(edge);
            s.graph.addEdge(edge)

            counter++
        }

    });


    // Carrega o grafo no sigma
    s.graph.read(graph);

    // Faz o sigma criar o grafo
    s.refresh();

    // inicia o algoritmo de espacialização
    s.startForceAtlas2();

    // para o algoritmo apos 10s
    window.setTimeout(function() {s.killForceAtlas2()}, 10000);

    //console.log('testing!!!!')

    //console.log(graph)

});
