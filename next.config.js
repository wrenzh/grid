/** @type {import('next').NextConfig} */
const nextConfig = {
    rewrites: async () => {
	return   [
	    {
		source: "/api/:path*",
		destination:
		process.env.NODE_ENV === "development"
		    ? "http://127.0.0.1:8000/api/:path*"
		    : "http://aghub:8000/api/:path*",
	    },
	    {
		source: "/docs",
		destination:
		process.env.NODE_ENV === "development"
		    ? "http://127.0.0.1:8000/docs"
		    : "http://aghub:8000/api/docs",
	    },
	    {
		source: "/openapi.json",
		destination:
		process.env.NODE_ENV === "development"
		    ? "http://127.0.0.1:8000/openapi.json"
		    : "http://aghub:8000/api/openapi.json",
	    },
	];
    },
    output: 'standalone',
};

module.exports = nextConfig
